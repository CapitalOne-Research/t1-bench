from typing import Any

from t1_plus_plus.schema.kayak.modify_kayak_reservation import ModifyKayakReservationInputModel, ModifyKayakReservationOutputModel
from t1_plus_plus.schema.kayak.kayak_reservation_db import global_kayak_reservation_db


def modify_kayak_reservation(**kwargs: Any) -> ModifyKayakReservationOutputModel:
    """
    Modifies the date, time, or duration of an existing kayak reservation.
    """
    try:
        mod_data = ModifyKayakReservationInputModel.model_validate(kwargs)
    except Exception as e:
        return ModifyKayakReservationOutputModel(
            status="error", message=f"Validation error: {str(e)}"
        )

    # 1. Ensure at least one field is being modified
    if not any([mod_data.new_date, mod_data.new_start_time, mod_data.new_duration]):
        return ModifyKayakReservationOutputModel(
            status="error", message="No new date, time, or duration provided to modify."
        )

    # 2. Fetch the reservation
    reservation = global_kayak_reservation_db.get_reservation(mod_data.booking_id)
    if not reservation:
        return ModifyKayakReservationOutputModel(
            status="error", message=f"No reservation found with ID {mod_data.booking_id}."
        )

    # 3. Verify Ownership & Status
    if reservation.user_id != mod_data.user_id:
        return ModifyKayakReservationOutputModel(
            status="error", message="User ID does not match the reservation owner."
        )
    if reservation.status == "Cancelled":
        return ModifyKayakReservationOutputModel(
            status="error", message="Cannot modify a cancelled reservation."
        )

    # 4. Apply Modifications
    changes_made = []

    if mod_data.new_date:
        reservation.date = mod_data.new_date
        changes_made.append(f"date to {mod_data.new_date}")

    if mod_data.new_start_time:
        reservation.start_time = mod_data.new_start_time
        changes_made.append(f"time to {mod_data.new_start_time}")

    if mod_data.new_duration and mod_data.new_duration != reservation.duration:
        # Calculate the base hourly rate using the old totals
        hourly_rate = reservation.total_cost / reservation.duration

        # Apply new duration and recalculate total
        reservation.duration = mod_data.new_duration
        reservation.total_cost = hourly_rate * mod_data.new_duration
        changes_made.append(f"duration to {mod_data.new_duration} hours")

    # Save changes back to DB
    global_kayak_reservation_db.add_reservation(reservation)

    change_summary = ", ".join(changes_made)
    return ModifyKayakReservationOutputModel(
        status="success",
        message=f"Successfully updated reservation {mod_data.booking_id}. Changed: {change_summary}.",
        booking_id=reservation.booking_id,
        updated_total_cost=reservation.total_cost
    )
