"""Support for Southern Company sensors."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import datetime

import southern_company_api

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_USERNAME, CURRENCY_DOLLAR, UnitOfEnergy
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import NicorGasCoordinator, SouthernCompanyCoordinator


@dataclass(frozen=True)
class SouthernCompanyEntityDescriptionMixin:
    """Mixin for required keys."""

    value_fn: Callable[[southern_company_api.account.MonthlyUsage], str | float]


@dataclass(frozen=True)
class SouthernCompanyEntityDescription(
    SensorEntityDescription, SouthernCompanyEntityDescriptionMixin
):
    """Describes Southern Company sensor entity."""


SENSORS: tuple[SouthernCompanyEntityDescription, ...] = (
    SouthernCompanyEntityDescription(
        key="dollars_to_date",
        name="Monthly cost",
        device_class=SensorDeviceClass.MONETARY,
        suggested_display_precision=2,
        value_fn=lambda data: data.dollars_to_date,
        native_unit_of_measurement=CURRENCY_DOLLAR,
    ),
    SouthernCompanyEntityDescription(
        key="total_kwh_used",
        name="Monthly consumption",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda data: data.total_kwh_used,
    ),
    SouthernCompanyEntityDescription(
        key="average_daily_cost",
        name="Average daily cost",
        device_class=SensorDeviceClass.MONETARY,
        value_fn=lambda data: data.average_daily_cost,
        native_unit_of_measurement=CURRENCY_DOLLAR,
    ),
    SouthernCompanyEntityDescription(
        key="average_daily_usage",
        name="Average daily usage",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        value_fn=lambda data: data.average_daily_usage,
    ),
    SouthernCompanyEntityDescription(
        key="projected_usage_high",
        name="Higher projected monthly usage",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL,
        value_fn=lambda data: data.projected_usage_high,
    ),
    SouthernCompanyEntityDescription(
        key="projected_usage_low",
        name="Lower projected monthly usage",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL,
        value_fn=lambda data: data.projected_usage_low,
    ),
    SouthernCompanyEntityDescription(
        key="projected_bill_amount_low",
        name="Lower projected monthly cost",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        value_fn=lambda data: data.projected_bill_amount_low,
        native_unit_of_measurement=CURRENCY_DOLLAR,
    ),
    SouthernCompanyEntityDescription(
        key="projected_bill_amount_high",
        name="Higher projected monthly cost",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        value_fn=lambda data: data.projected_bill_amount_high,
        native_unit_of_measurement=CURRENCY_DOLLAR,
    ),
)


# ---------------------------------------------------------------------------
# Nicor Gas sensors
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class NicorGasEntityDescriptionMixin:
    """Mixin for required keys."""

    value_fn: Callable[
        [southern_company_api.NicorUsageHistory],
        StateType | datetime.date,
    ]


@dataclass(frozen=True)
class NicorGasEntityDescription(
    SensorEntityDescription, NicorGasEntityDescriptionMixin
):
    """Describes Nicor Gas sensor entity."""


def _current_billing_period_therms(
    data: southern_company_api.NicorUsageHistory,
) -> float | None:
    if not data.daily_usage:
        return None
    current_period = max(data.daily_usage, key=lambda d: d.date).billing_period
    return sum(d.therms for d in data.daily_usage if d.billing_period == current_period)


def _current_billing_period_cost(
    data: southern_company_api.NicorUsageHistory,
) -> float | None:
    if not data.daily_usage:
        return None
    current_period = max(data.daily_usage, key=lambda d: d.date).billing_period
    return sum(d.cost for d in data.daily_usage if d.billing_period == current_period)


def _most_recent_daily_therms(
    data: southern_company_api.NicorUsageHistory,
) -> float | None:
    if not data.daily_usage:
        return None
    return max(data.daily_usage, key=lambda d: d.date).therms


def _most_recent_daily_cost(
    data: southern_company_api.NicorUsageHistory,
) -> float | None:
    if not data.daily_usage:
        return None
    return max(data.daily_usage, key=lambda d: d.date).cost


def _next_meter_read_date(
    data: southern_company_api.NicorUsageHistory,
) -> datetime.date | None:
    if not data.meter_info:
        return None
    return data.meter_info.next_read_date.date()


NICOR_SENSORS: tuple[NicorGasEntityDescription, ...] = (
    NicorGasEntityDescription(
        key="billing_period_therms",
        name="Billing period therms",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement="therm",
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=_current_billing_period_therms,
    ),
    NicorGasEntityDescription(
        key="billing_period_cost",
        name="Billing period cost",
        device_class=SensorDeviceClass.MONETARY,
        suggested_display_precision=2,
        native_unit_of_measurement=CURRENCY_DOLLAR,
        value_fn=_current_billing_period_cost,
    ),
    NicorGasEntityDescription(
        key="projected_bill",
        name="Projected bill",
        device_class=SensorDeviceClass.MONETARY,
        suggested_display_precision=2,
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement=CURRENCY_DOLLAR,
        value_fn=lambda data: data.projected_bill.high_amount,
    ),
    NicorGasEntityDescription(
        key="daily_therms",
        name="Daily therms",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement="therm",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_most_recent_daily_therms,
    ),
    NicorGasEntityDescription(
        key="daily_cost",
        name="Daily cost",
        device_class=SensorDeviceClass.MONETARY,
        suggested_display_precision=2,
        native_unit_of_measurement=CURRENCY_DOLLAR,
        value_fn=_most_recent_daily_cost,
    ),
    NicorGasEntityDescription(
        key="next_meter_read_date",
        name="Next meter read date",
        device_class=SensorDeviceClass.DATE,
        value_fn=_next_meter_read_date,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the Southern Company sensor."""

    coordinator = hass.data[DOMAIN][entry.entry_id]

    if isinstance(coordinator, NicorGasCoordinator):
        data = coordinator.data
        if data.meter_info:
            meter_id = data.meter_info.meter_number
        else:
            meter_id = entry.data[CONF_USERNAME]
        device = DeviceInfo(
            identifiers={(DOMAIN, f"nicor_gas_{meter_id}")},
            name="Nicor Gas",
            manufacturer="Nicor Gas",
        )
        async_add_entities(
            [
                NicorGasSensor(coordinator, sensor, meter_id, device)
                for sensor in NICOR_SENSORS
            ]
        )
        return

    southern_company_coordinator: SouthernCompanyCoordinator = coordinator
    southern_company_connection = southern_company_coordinator.api
    entities: list[SouthernCompanySensor] = []
    for account in await southern_company_connection.accounts:
        device = DeviceInfo(
            identifiers={(DOMAIN, account.number)},
            name=f"Account {account.number}",
            manufacturer="Southern Company",
        )

        # entities.append(SouthernCompanySensor(account, coordinator, sensor, device))
        entities.extend(
            [
                SouthernCompanySensor(
                    account, southern_company_coordinator, sensor, device
                )
                for sensor in SENSORS
            ]
        )

    async_add_entities(entities)


class SouthernCompanySensor(
    SensorEntity, CoordinatorEntity[SouthernCompanyCoordinator]
):
    """Representation of a Southern company sensor."""

    def __init__(
        self,
        account: southern_company_api.Account,
        coordinator: SouthernCompanyCoordinator,
        description: SouthernCompanyEntityDescription,
        device: DeviceInfo,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description: SouthernCompanyEntityDescription = description
        self._account = account
        self._attr_unique_id = f"{self._account.number}_{description.key}"
        self._attr_device_info = device
        self._sensor_data = None

    @property
    def native_value(self) -> StateType:
        """Return the state."""
        if self.coordinator.data is not None:
            return self.entity_description.value_fn(
                self.coordinator.data[self._account.number]
            )
        return None


class NicorGasSensor(SensorEntity, CoordinatorEntity[NicorGasCoordinator]):
    """Representation of a Nicor Gas sensor."""

    def __init__(
        self,
        coordinator: NicorGasCoordinator,
        description: NicorGasEntityDescription,
        meter_id: str,
        device: DeviceInfo,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description: NicorGasEntityDescription = description
        self._attr_unique_id = f"nicor_gas_{meter_id}_{description.key}"
        self._attr_device_info = device

    @property
    def native_value(self) -> StateType | datetime.date:
        """Return the state."""
        if self.coordinator.data is not None:
            return self.entity_description.value_fn(self.coordinator.data)
        return None
