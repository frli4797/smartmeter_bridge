import json
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock
import sys
import logging


def install_dependency_stubs() -> None:
    requests_module = types.ModuleType("requests")
    requests_module.Timeout = type("Timeout", (Exception,), {})
    requests_module.ConnectionError = type("ConnectionError", (Exception,), {})

    class Session:
        def __init__(self) -> None:
            self.headers = {}

        def close(self) -> None:
            return None

    class Response:
        def __init__(self) -> None:
            self.status_code = 200

        def json(self):
            return {}

    requests_module.Session = Session
    requests_module.Response = Response
    sys.modules.setdefault("requests", requests_module)

    yaml_module = types.ModuleType("yaml")
    yaml_module.YAMLError = Exception
    yaml_module.safe_load = lambda _data: {}
    sys.modules.setdefault("yaml", yaml_module)

    pymodbus_module = types.ModuleType("pymodbus")
    datastore_module = types.ModuleType("pymodbus.datastore")
    server_module = types.ModuleType("pymodbus.server")

    class ModbusSequentialDataBlock:
        def __init__(self, address: int, values: list[int]) -> None:
            self.address = address
            self.values = list(values)

        def getValues(self, address: int, count: int = 1) -> list[int]:
            return self.values[address:address + count]

        def setValues(self, address: int, values: list[int]) -> None:
            for index, value in enumerate(values):
                position = address + index
                if position >= len(self.values):
                    self.values.extend([0] * (position - len(self.values) + 1))
                self.values[position] = value

    class ModbusDeviceContext:
        def __init__(self, **kwargs) -> None:
            self.kwargs = kwargs

    class ModbusServerContext:
        def __init__(self, **kwargs) -> None:
            self.kwargs = kwargs

    datastore_module.ModbusSequentialDataBlock = ModbusSequentialDataBlock
    datastore_module.ModbusDeviceContext = ModbusDeviceContext
    datastore_module.ModbusServerContext = ModbusServerContext
    server_module.StartTcpServer = lambda *args, **kwargs: None

    sys.modules.setdefault("pymodbus", pymodbus_module)
    sys.modules.setdefault("pymodbus.datastore", datastore_module)
    sys.modules.setdefault("pymodbus.server", server_module)


install_dependency_stubs()

from smartmeter_bridge import modbus_bridge


class JsonFormatterTests(unittest.TestCase):
    def test_log_payload_includes_victorialogs_message_field(self) -> None:
        formatter = modbus_bridge.JsonFormatter()
        record = logging.LogRecord(
            "ha_em420",
            logging.INFO,
            __file__,
            1,
            "Home Assistant polling healthy",
            (),
            None,
        )

        payload = json.loads(formatter.format(record))

        self.assertEqual(payload["_msg"], "Home Assistant polling healthy")
        self.assertEqual(payload["message"], "Home Assistant polling healthy")


def make_config() -> modbus_bridge.HomeAssistantConfig:
    return modbus_bridge.HomeAssistantConfig(
        url="http://homeassistant.local:8123",
        token="token",
        entities=modbus_bridge.HomeAssistantEntities(
            total_power_w="sensor.total_power_w",
            total_pf="sensor.total_pf",
            total_import_kwh="sensor.total_import_kwh",
            l1_v="sensor.l1_v",
            l2_v="sensor.l2_v",
            l3_v="sensor.l3_v",
            l1_a="sensor.l1_a",
            l2_a="sensor.l2_a",
            l3_a="sensor.l3_a",
        ),
        source="test",
    )


class MainStartupTests(unittest.TestCase):
    def run_main(
        self,
        client: mock.Mock,
        health_path: Path,
    ) -> tuple[mock.Mock, mock.Mock]:
        thread = mock.Mock()
        with (
            mock.patch(
                "sys.argv",
                [
                    "modbus_bridge.py",
                    "--health-path",
                    str(health_path),
                ],
            ),
            mock.patch.object(
                modbus_bridge, "load_homeassistant_config", return_value=make_config()
            ),
            mock.patch.object(modbus_bridge, "HomeAssistantClient", return_value=client),
            mock.patch.object(
                modbus_bridge, "StartTcpServer", side_effect=KeyboardInterrupt
            ) as start_server,
            mock.patch.object(modbus_bridge.signal, "signal"),
            mock.patch.object(modbus_bridge.threading, "Thread", return_value=thread),
        ):
            modbus_bridge.main()
        return start_server, thread

    def test_main_keeps_running_when_home_assistant_is_temporarily_unavailable(self) -> None:
        client = mock.Mock()
        client.validate_access.side_effect = modbus_bridge.HomeAssistantError(
            "Home Assistant request failed for /api/ with HTTP 502"
        )
        client.token_fingerprint = "fingerprint"

        with tempfile.TemporaryDirectory() as temp_dir:
            start_server, thread = self.run_main(
                client=client,
                health_path=Path(temp_dir) / "health.json",
            )

        start_server.assert_called_once()
        client.validate_entities.assert_not_called()
        client.close.assert_called_once()
        thread.start.assert_called_once()
        thread.join.assert_called_once()

    def test_main_still_exits_on_home_assistant_auth_failure(self) -> None:
        client = mock.Mock()
        client.validate_access.side_effect = modbus_bridge.HomeAssistantAuthError(
            "token rejected"
        )
        client.token_fingerprint = "fingerprint"

        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaises(SystemExit) as exc:
                self.run_main(
                    client=client,
                    health_path=Path(temp_dir) / "health.json",
                )

        self.assertEqual(exc.exception.code, 1)
        client.close.assert_called_once()


class PowerFactorCalculationTests(unittest.TestCase):
    def test_calculate_three_phase_power_factor(self) -> None:
        power_factor = modbus_bridge.calculate_three_phase_power_factor(
            total_power_w=9000.0,
            l1_v=230.0,
            l2_v=230.0,
            l3_v=230.0,
            l1_a=14.0,
            l2_a=14.0,
            l3_a=14.0,
        )

        self.assertAlmostEqual(power_factor, 0.9316770186, places=6)

    def test_load_homeassistant_config_allows_missing_total_pf_when_calculation_enabled(self) -> None:
        config = {
            "HA_URL": "http://homeassistant.local:8123",
            "HA_TOKEN": "token",
            "CALCULATE_POWER_FACTOR": "true",
            "HA_ENTITY_TOTAL_POWER_W": "sensor.total_power_w",
            "HA_ENTITY_TOTAL_IMPORT_KWH": "sensor.total_import_kwh",
            "HA_ENTITY_L1_V": "sensor.l1_v",
            "HA_ENTITY_L2_V": "sensor.l2_v",
            "HA_ENTITY_L3_V": "sensor.l3_v",
            "HA_ENTITY_L1_A": "sensor.l1_a",
            "HA_ENTITY_L2_A": "sensor.l2_a",
            "HA_ENTITY_L3_A": "sensor.l3_a",
        }

        with mock.patch.dict(modbus_bridge.os.environ, config, clear=True):
            loaded = modbus_bridge.load_homeassistant_config(Path("missing.yaml"))

        self.assertIsNone(loaded.entities.total_pf)

    def test_load_homeassistant_config_treats_null_total_pf_as_missing_when_calculation_enabled(self) -> None:
        config = {
            "HA_URL": "http://homeassistant.local:8123",
            "HA_TOKEN": "token",
            "CALCULATE_POWER_FACTOR": "true",
            "HA_ENTITY_TOTAL_POWER_W": "sensor.total_power_w",
            "HA_ENTITY_TOTAL_PF": "null",
            "HA_ENTITY_TOTAL_IMPORT_KWH": "sensor.total_import_kwh",
            "HA_ENTITY_L1_V": "sensor.l1_v",
            "HA_ENTITY_L2_V": "sensor.l2_v",
            "HA_ENTITY_L3_V": "sensor.l3_v",
            "HA_ENTITY_L1_A": "sensor.l1_a",
            "HA_ENTITY_L2_A": "sensor.l2_a",
            "HA_ENTITY_L3_A": "sensor.l3_a",
        }

        with mock.patch.dict(modbus_bridge.os.environ, config, clear=True):
            loaded = modbus_bridge.load_homeassistant_config(Path("missing.yaml"))

        self.assertIsNone(loaded.entities.total_pf)

    def test_load_homeassistant_config_rejects_null_total_pf_when_total_pf_is_required(self) -> None:
        config = {
            "HA_URL": "http://homeassistant.local:8123",
            "HA_TOKEN": "token",
            "HA_ENTITY_TOTAL_POWER_W": "sensor.total_power_w",
            "HA_ENTITY_TOTAL_PF": "null",
            "HA_ENTITY_TOTAL_IMPORT_KWH": "sensor.total_import_kwh",
            "HA_ENTITY_L1_V": "sensor.l1_v",
            "HA_ENTITY_L2_V": "sensor.l2_v",
            "HA_ENTITY_L3_V": "sensor.l3_v",
            "HA_ENTITY_L1_A": "sensor.l1_a",
            "HA_ENTITY_L2_A": "sensor.l2_a",
            "HA_ENTITY_L3_A": "sensor.l3_a",
        }

        with mock.patch.dict(modbus_bridge.os.environ, config, clear=True):
            with self.assertRaisesRegex(ValueError, "total_pf"):
                modbus_bridge.load_homeassistant_config(Path("missing.yaml"))


class PollFailureReporterTests(unittest.TestCase):
    def test_startup_failures_are_logged_once_at_info_during_grace(self) -> None:
        reporter = modbus_bridge.PollFailureReporter(
            startup_grace_s=120.0,
            transient_log_interval_s=60.0,
        )
        failure = modbus_bridge.HomeAssistantConnectivityError("not ready")

        with (
            mock.patch.object(modbus_bridge.time, "time", side_effect=[0.0, 2.0, 30.0]),
            mock.patch.object(modbus_bridge, "log_event") as log_event,
        ):
            reporter.log_homeassistant_failure(
                failure,
                consecutive_failures=1,
                retry_delay_s=2.0,
            )
            reporter.log_homeassistant_failure(
                failure,
                consecutive_failures=2,
                retry_delay_s=4.0,
            )
            reporter.log_homeassistant_failure(
                failure,
                consecutive_failures=3,
                retry_delay_s=8.0,
            )

        log_event.assert_called_once()
        self.assertEqual(log_event.call_args.args[0], logging.INFO)
        self.assertEqual(log_event.call_args.kwargs["event"], "ha_poll_waiting")

    def test_persistent_failures_are_escalated_after_startup_grace(self) -> None:
        reporter = modbus_bridge.PollFailureReporter(
            startup_grace_s=120.0,
            transient_log_interval_s=60.0,
            persistent_log_interval_s=60.0,
        )
        failure = modbus_bridge.HomeAssistantError("HTTP 502")

        with (
            mock.patch.object(modbus_bridge.time, "time", side_effect=[0.0, 30.0, 121.0]),
            mock.patch.object(modbus_bridge, "log_event") as log_event,
        ):
            reporter.log_homeassistant_failure(
                failure,
                consecutive_failures=1,
                retry_delay_s=2.0,
            )
            reporter.log_homeassistant_failure(
                failure,
                consecutive_failures=2,
                retry_delay_s=4.0,
            )
            reporter.log_homeassistant_failure(
                failure,
                consecutive_failures=3,
                retry_delay_s=8.0,
            )

        self.assertEqual(log_event.call_count, 2)
        self.assertEqual(log_event.call_args.args[0], logging.WARNING)
        self.assertEqual(log_event.call_args.kwargs["event"], "ha_poll_failure")
        self.assertEqual(log_event.call_args.kwargs["suppressed_failures"], 1)

    def test_recovery_logs_suppressed_failures(self) -> None:
        reporter = modbus_bridge.PollFailureReporter(
            startup_grace_s=120.0,
            transient_log_interval_s=60.0,
        )
        failure = modbus_bridge.HomeAssistantConnectivityError("not ready")

        with (
            mock.patch.object(modbus_bridge.time, "time", side_effect=[0.0, 30.0, 45.0]),
            mock.patch.object(modbus_bridge, "log_event") as log_event,
        ):
            reporter.log_homeassistant_failure(
                failure,
                consecutive_failures=1,
                retry_delay_s=2.0,
            )
            reporter.log_homeassistant_failure(
                failure,
                consecutive_failures=2,
                retry_delay_s=4.0,
            )
            reporter.log_recovered(consecutive_failures=2)

        self.assertEqual(log_event.call_args.args[0], logging.INFO)
        self.assertEqual(log_event.call_args.kwargs["event"], "ha_poll_recovered")
        self.assertEqual(log_event.call_args.kwargs["suppressed_failures"], 1)


class MeterRegisterMapperTests(unittest.TestCase):
    def test_updater_loop_uses_meter_mapper_interface(self) -> None:
        block = modbus_bridge.LoggingBlock(
            "HR",
            0,
            modbus_bridge.allocate_registers(8),
        )
        client = mock.Mock()
        client.token_fingerprint = "fingerprint"
        entities = make_config().entities
        health_state = mock.Mock()
        reporter = modbus_bridge.PollReporter()
        stop_event = modbus_bridge.threading.Event()
        calls = []

        class RecordingMapper(modbus_bridge.MeterRegisterMapper):
            meter_type = "recording"
            register_count = 8

            def initialize(
                self,
                hr_block: modbus_bridge.LoggingBlock,
                frequency_hz: float = 50.0,
            ) -> None:
                return None

            def update_from_homeassistant(
                self,
                hr_block: modbus_bridge.LoggingBlock,
                ha: modbus_bridge.HomeAssistantClient,
                entities: modbus_bridge.HomeAssistantEntities,
                reporter: modbus_bridge.PollReporter,
                frequency_hz: float = 50.0,
                use_phase_sum_for_total_power: bool = False,
                calculate_power_factor: bool = False,
            ) -> None:
                calls.append(
                    (
                        hr_block,
                        ha,
                        entities,
                        reporter,
                        frequency_hz,
                        use_phase_sum_for_total_power,
                        calculate_power_factor,
                    )
                )
                stop_event.set()

        with mock.patch.dict(modbus_bridge.os.environ, {}, clear=True):
            modbus_bridge.updater_loop(
                hr_block=block,
                ha=client,
                entities=entities,
                meter_mapper=RecordingMapper(),
                health_state=health_state,
                reporter=reporter,
                stop_event=stop_event,
                interval_s=0.01,
                frequency_hz=60.0,
                use_phase_sum_for_total_power=True,
                max_backoff_s=0.01,
                startup_grace_s=1.0,
            )

        self.assertEqual(len(calls), 1)
        self.assertIs(calls[0][0], block)
        self.assertIs(calls[0][1], client)
        self.assertIs(calls[0][2], entities)
        self.assertIs(calls[0][3], reporter)
        self.assertEqual(calls[0][4], 60.0)
        self.assertTrue(calls[0][5])
        self.assertFalse(calls[0][6])
        health_state.mark_success.assert_called_once()


class HomeAssistantRegisterUpdateTests(unittest.TestCase):
    def make_client(self, states: dict[str, object]) -> modbus_bridge.HomeAssistantClient:
        client = modbus_bridge.HomeAssistantClient("http://homeassistant.local:8123", "token")

        def get_state(entity_id: str) -> dict[str, object]:
            return {"state": states[entity_id]}

        client.get_state = get_state
        return client

    def make_block(self) -> modbus_bridge.LoggingBlock:
        block = modbus_bridge.LoggingBlock(
            "HR",
            0,
            modbus_bridge.allocate_registers(2000),
        )
        modbus_bridge.initialize_em420_defaults(block)
        return block

    def make_states(self, **overrides: object) -> dict[str, object]:
        states: dict[str, object] = {
            "sensor.total_power_w": "0",
            "sensor.total_pf": "1",
            "sensor.total_import_kwh": "123.45",
            "sensor.l1_v": "230",
            "sensor.l2_v": "230",
            "sensor.l3_v": "230",
            "sensor.l1_a": "0",
            "sensor.l2_a": "0",
            "sensor.l3_a": "0",
        }
        states.update(overrides)
        return states

    def test_zero_values_are_valid_and_enable_modbus_reads(self) -> None:
        block = self.make_block()
        client = self.make_client(self.make_states())

        modbus_bridge.update_em420_registers_from_ha(
            hr_block=block,
            ha=client,
            entities=make_config().entities,
            reporter=modbus_bridge.PollReporter(),
        )

        self.assertEqual(block.getValues(modbus_bridge.idx(0), 2), [0, 0])
        self.assertEqual(block.getValues(modbus_bridge.idx(60), 2), [0, 0])

    def test_unavailable_required_values_keep_serving_default_modbus_reads(self) -> None:
        block = self.make_block()
        client = self.make_client(
            self.make_states(**{"sensor.total_power_w": "unavailable"})
        )

        with self.assertRaises(modbus_bridge.HomeAssistantEntityError):
            modbus_bridge.update_em420_registers_from_ha(
                hr_block=block,
                ha=client,
                entities=make_config().entities,
                reporter=modbus_bridge.PollReporter(),
            )

        self.assertEqual(block.getValues(modbus_bridge.idx(0), 2), [0, 0])

    def test_modbus_reads_resume_after_unavailable_value_recovers(self) -> None:
        block = self.make_block()
        states = self.make_states(**{"sensor.total_power_w": "unavailable"})
        client = self.make_client(states)

        with self.assertRaises(modbus_bridge.HomeAssistantEntityError):
            modbus_bridge.update_em420_registers_from_ha(
                hr_block=block,
                ha=client,
                entities=make_config().entities,
                reporter=modbus_bridge.PollReporter(),
            )
        self.assertEqual(block.getValues(modbus_bridge.idx(0), 2), [0, 0])

        states["sensor.total_power_w"] = "1200"
        modbus_bridge.update_em420_registers_from_ha(
            hr_block=block,
            ha=client,
            entities=make_config().entities,
            reporter=modbus_bridge.PollReporter(),
        )

        self.assertEqual(block.getValues(modbus_bridge.idx(0), 2), [0, 12000])


if __name__ == "__main__":
    unittest.main()
