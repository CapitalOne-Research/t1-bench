from datetime import datetime
from t1_plus_plus.schema.vehicle_rental.vehicle_rental_reservation import (
    ModifyRentalReservationInputModel,
    ModifyRentalReservationOutputModel,
)
from t1_plus_plus.schema.vehicle_rental.vehicle_rental_reservation_db import (
    global_rental_reservations_db,
)


def modify_vehicle_rental_reservation(
    **kwargs: ModifyRentalReservationInputModel,
) -> ModifyRentalReservationOutputModel:
    """
    Description:
        Modifies an existing rental. Can update dates or add insurance coverage.

    Examples:
    >>> # Usage Example:
    modify_vehicle_rental_reservation(user_id="U123", reservation_id="REN-AB12CD34", new_end_date="2026-05-08")

    >>> # Usage Example:
    modify_vehicle_rental_reservation(user_id="U456", reservation_id="REN-EF56GH78", new_start_date="2026-06-12", new_end_date="2026-06-18")

    Returns:
        ModifyRentalReservationOutputModel: Output object containing status, message, reservation_id, and new_charge.
    """
    input_data = ModifyRentalReservationInputModel.model_validate(kwargs)

    # Retrieve from global db
    res = global_rental_reservations_db.get_reservation(input_data.reservation_id)

    if not res:
        return ModifyRentalReservationOutputModel(
            status="error", message="Reservation ID not found."
        )

    if res.user_id != input_data.user_id:
        return ModifyRentalReservationOutputModel(
            status="error", message="User ID does not match the reservation record."
        )

    if res.status != "Active":
        return ModifyRentalReservationOutputModel(
            status="error",
            message="Cannot modify an inactive or cancelled reservation.",
        )

    # Update Dates
    if input_data.new_start_date:
        res.start_date = datetime.strptime(input_data.new_start_date, "%Y-%m-%d")

    if input_data.new_end_date:
        res.end_date = datetime.strptime(input_data.new_end_date, "%Y-%m-%d")

    # Recalculate total if dates changed (Optional: based on daily rate)
    new_days = (res.end_date - res.start_date).days
    res.reservation_charge = float(res.base_price_per_day * new_days)
    if getattr(res, "has_insurance", False):
        res.reservation_charge += 25.00

    global_rental_reservations_db.add_reservation(res)

    return ModifyRentalReservationOutputModel(
        status="success",
        message="Rental reservation successfully modified.",
        reservation_id=res.reservation_id,
        new_charge=res.reservation_charge,
    )
