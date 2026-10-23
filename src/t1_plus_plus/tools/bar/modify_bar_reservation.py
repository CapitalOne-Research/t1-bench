import hashlib
from datetime import datetime

from t1_plus_plus.schema.bar.bar_reservation import (
    ModifyBarReservationInputModel,
    ModifyBarReservationOutputModel,
)
from t1_plus_plus.schema.bar.bar_reservation_db import global_bar_reservations_db


def modify_bar_reservation(
    **kwargs: ModifyBarReservationInputModel,
) -> ModifyBarReservationOutputModel:
    """
    Description:
        Use this tool to modify an existing bar reservation. Can change dates (if available), adjust guest count, or upgrade the reservation to a VIP private room.

    Examples:
    >>> # Usage Example:
    modify_bar_reservation(user_id="U123", reservation_id="RES-ABC12345", new_event_datetime="2026-05-12 21:00")

    >>> # Usage Example:
    modify_bar_reservation(user_id="U789", reservation_id="RES-DEF67890", new_number_guests=6, upgrade_vip_room=True)

    Returns:
        ModifyBarReservationOutputModel: Output object which contains the modification status, updated reservation ID, new charge, and VIP status.
    """
    input_data = ModifyBarReservationInputModel.model_validate(kwargs)

    # Retrieve from global db
    res = global_bar_reservations_db.get_reservation(input_data.reservation_id)

    if not res:
        return ModifyBarReservationOutputModel(
            status="error", message="Reservation ID not found."
        )

    if res.user_id != input_data.user_id:
        return ModifyBarReservationOutputModel(
            status="error", message="User ID does not match the reservation."
        )

    if res.status != "Active":
        return ModifyBarReservationOutputModel(
            status="error",
            message="Cannot modify an inactive or cancelled reservation.",
        )

    if input_data.new_event_datetime:
        res.event_datetime = datetime.strptime(
            input_data.new_event_datetime, "%Y-%m-%d %H:%M"
        )
        # Recompute reservation_id since it is derived from user_id:venue_id:event_datetime
        seed = f"{res.user_id}:{res.venue_id}:{input_data.new_event_datetime}"
        new_res_id = f"RES-{hashlib.md5(seed.encode()).hexdigest()[:8].upper()}"
        global_bar_reservations_db.delete_reservation(res.reservation_id)
        res.reservation_id = new_res_id

    if input_data.new_number_guests:
        res.number_guests = input_data.new_number_guests

    if input_data.upgrade_vip_room and not res.is_vip_room:
        res.is_vip_room = True
        res.reservation_charge += 100.00  # VIP upgrade fee

    # Re-save to ensure the DB registers the updated Pydantic object
    global_bar_reservations_db.add_reservation(res)

    return ModifyBarReservationOutputModel(
        status="success",
        message="Reservation successfully modified.",
        reservation_id=res.reservation_id,
        new_charge=res.reservation_charge,
        is_vip=res.is_vip_room,
    )
