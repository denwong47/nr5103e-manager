import http
from typing import Any

from pydantic import BaseModel, Field, computed_field

from .protocol import GLOBAL_MODEL_CONFIG, NR5103EWebEndpoint


class CellWanStatusQuery(BaseModel):
    """
    The query parameters for the cell WAN status endpoint.
    """

    model_config = GLOBAL_MODEL_CONFIG

    @computed_field()
    def oid(self) -> str:
        """
        The object identifier (OID) for the cell WAN status endpoint.
        """
        return "cellwan_status"


class CellWanStatusObject(BaseModel):
    """
    A single cell WAN status object from the NR5103E response payload.
    """

    model_config = GLOBAL_MODEL_CONFIG

    cell_roaming_enable: bool = Field(validation_alias="CELL_Roaming_Enable")
    intf_status: str = Field(validation_alias="INTF_Status")
    intf_imei: str = Field(validation_alias="INTF_IMEI")
    intf_current_access_technology: str = Field(
        validation_alias="INTF_Current_Access_Technology"
    )
    intf_network_in_use: str = Field(validation_alias="INTF_Network_In_Use")
    intf_rssi: int = Field(validation_alias="INTF_RSSI")
    intf_supported_bands: str = Field(validation_alias="INTF_Supported_Bands")
    intf_current_band: str = Field(validation_alias="INTF_Current_Band")
    intf_cell_id: int = Field(validation_alias="INTF_Cell_ID")
    intf_phy_cell_id: int = Field(validation_alias="INTF_PhyCell_ID")
    intf_uplink_bandwidth: str = Field(validation_alias="INTF_Uplink_Bandwidth")
    intf_downlink_bandwidth: str = Field(validation_alias="INTF_Downlink_Bandwidth")
    intf_rfcn: str = Field(validation_alias="INTF_RFCN")
    intf_rsrp: int = Field(validation_alias="INTF_RSRP")
    intf_rsrq: int = Field(validation_alias="INTF_RSRQ")
    intf_rscp: int = Field(validation_alias="INTF_RSCP")
    intf_ec_no: int = Field(validation_alias="INTF_EcNo")
    intf_tac: int = Field(validation_alias="INTF_TAC")
    intf_lac: int = Field(validation_alias="INTF_LAC")
    intf_rac: int = Field(validation_alias="INTF_RAC")
    intf_bsic: int = Field(validation_alias="INTF_BSIC")
    intf_sinr: int = Field(validation_alias="INTF_SINR")
    intf_cqi: int = Field(validation_alias="INTF_CQI")
    intf_mcs: int = Field(validation_alias="INTF_MCS")
    intf_ri: int = Field(validation_alias="INTF_RI")
    intf_pmi: int = Field(validation_alias="INTF_PMI")
    intf_module_software_version: str = Field(
        validation_alias="INTF_Module_Software_Version"
    )
    usim_status: str = Field(validation_alias="USIM_Status")
    usim_imsi: str = Field(validation_alias="USIM_IMSI")
    usim_iccid: str = Field(validation_alias="USIM_ICCID")
    usim_pin_protection: bool = Field(validation_alias="USIM_PIN_Protection")
    usim_pin_remaining_attempts: int = Field(
        validation_alias="USIM_PIN_Remaining_Attempts"
    )
    passthru_enable: bool = Field(validation_alias="Passthru_Enable")
    passthru_mode: str = Field(validation_alias="Passthru_Mode")
    passthru_mac_addr: str = Field(validation_alias="Passthru_MacAddr")
    nsa_enable: bool = Field(validation_alias="NSA_Enable")
    nsa_mcc: str = Field(validation_alias="NSA_MCC")
    nsa_mnc: str = Field(validation_alias="NSA_MNC")
    nsa_phy_cell_id: int = Field(validation_alias="NSA_PhyCellID")
    nsa_rfcn: int = Field(validation_alias="NSA_RFCN")
    nsa_band: str = Field(validation_alias="NSA_Band")
    nsa_rssi: int = Field(validation_alias="NSA_RSSI")
    nsa_uplink_bandwidth: str | None = Field(validation_alias="NSA_UplinkBandwidth")
    nsa_downlink_bandwidth: str | None = Field(validation_alias="NSA_DownlinkBandwidth")
    nsa_rsrp: int = Field(validation_alias="NSA_RSRP")
    nsa_rsrq: int = Field(validation_alias="NSA_RSRQ")
    nsa_sinr: int = Field(validation_alias="NSA_SINR")
    scc_info: list[dict[str, Any]] = Field(validation_alias="SCC_Info")


class CellWanStatusResponse(BaseModel):
    """
    The response from the NR5103E device for the cell WAN status endpoint.
    """

    model_config = GLOBAL_MODEL_CONFIG

    result: str = Field(
        ...,
        description="The result of the request, typically `ZCFG_SUCCESS` when successful.",
        alias="result",
    )
    reply_msg: str = Field(
        ...,
        description="Reply message from the router, if any.",
        alias="ReplyMsg",
    )
    reply_msg_multi_lang: str = Field(
        ...,
        description="Localized reply message from the router, if any.",
        alias="ReplyMsgMultiLang",
    )
    objects: list[CellWanStatusObject] = Field(
        ...,
        description="List of cell WAN status records.",
        alias="Object",
    )


cellwan_status_endpoint = NR5103EWebEndpoint[
    CellWanStatusQuery, None, CellWanStatusResponse
](
    path="/cgi-bin/DAL",
    method=http.HTTPMethod.GET,
    query_type=CellWanStatusQuery,
    body_type=None,
    response_type=CellWanStatusResponse,
)
"""
The NR5103E web endpoint for retrieving the cell WAN status from the device. This
endpoint uses a query parameter to specify the object identifier (OID) for the cell WAN
status, and returns a response containing the status information.
"""
