from datetime import datetime
from t1_plus_plus.schema.cruise.cruise_reservation import (
    ModifyCruiseReservationInputModel,
    ModifyCruiseReservationOutputModel,
)
from t1_plus_plus.schema.cruise.cruise_reservation_db import global_cruise_reservations_db

def modify_cruise_reservation(**kwargs: ModifyCruiseReservationInputModel) -> ModifyCruiseReservationOutputModel:
    """
    Description:
        Modifies an existing cruise reservation. Can change dates, adjust guest count,
        or upgrade the reservation to a Suite.
    """
    # 2. Validate Agent Input with Error Catching
    try:
        input_data = ModifyCruiseReservationInputModel.model_validate(kwargs)
    except Exception as e:
        return ModifyCruiseReservationOutputModel(
            status="error", message=f"Invalid input data: {str(e)}"
        )

    res = global_cruise_reservations_db.get_reservation(input_data.reservation_id)

    if not res:
        return ModifyCruiseReservationOutputModel(status="error", message="Reservation ID not found.")

    if res.user_id != input_data.user_id:
        return ModifyCruiseReservationOutputModel(status="error", message="User ID does not match the reservation.")

    if res.status != "Active":
        return ModifyCruiseReservationOutputModel(status="error", message="Cannot modify an inactive or cancelled reservation.")

    if input_data.new_departure_date:
        res.departure_date = datetime.strptime(input_data.new_departure_date, "%Y-%m-%d")

    if input_data.new_number_guests:
        res.number_guests = input_data.new_number_guests

    if input_data.upgrade_cabin and not res.is_upgraded:
        res.is_upgraded = True
        res.cabin_type = "Suite"
        res.reservation_charge += 500.00  # Cabin upgrade fee

    global_cruise_reservations_db.add_reservation(res)

    return ModifyCruiseReservationOutputModel(
        status="success",
        message="Cruise reservation successfully modified.",
        reservation_id=res.reservation_id,
        new_charge=res.reservation_charge,
        is_upgraded=res.is_upgraded,
    )
