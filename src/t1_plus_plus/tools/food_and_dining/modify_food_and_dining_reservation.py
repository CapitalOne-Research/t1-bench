from t1_plus_plus.schema.food_and_dining.food_and_dining_order import (
    ModifyReservationInputModel,
    ModifyReservationOutputModel,
)
from t1_plus_plus.schema.food_and_dining.food_and_dining_order_db import global_reservations_db
from t1_plus_plus.ontology.food_and_dining import PRIVATE_DINING_UPGRADE_FEE


def modify_food_and_dining_reservation(**kwargs) -> ModifyReservationOutputModel:
    """
    Description:
        Modify an existing dine-in reservation. Can update the guest count, price per person,
        or upgrade to private dining (+$50.00 fee). Only Active reservations can be modified.

    Examples:
    >>> # Usage Example:
    modify_food_and_dining_reservation(user_id="USR-DFEDBA29", reservation_id="RES-1A2946F9", new_number_guests=4)

    >>> # Usage Example:
    modify_food_and_dining_reservation(user_id="USR-4B4B4FCA", reservation_id="RES-7C762220", upgrade_private_dining=True)

    >>> # Usage Example:
    modify_food_and_dining_reservation(user_id="USR-58E33E81", reservation_id="RES-5A6BDC19", new_number_guests=4, new_price_per_person=32.0)

    Returns:
        ModifyReservationOutputModel: status, reservation_id, new_charge, has_private_dining.
    """
    try:
        input_data = ModifyReservationInputModel.model_validate(kwargs)
    except Exception as e:
        return ModifyReservationOutputModel(
            status="error", message=f"Invalid input data: {str(e)}"
        )

    reservation = global_reservations_db.get_reservation(input_data.reservation_id)
    if not reservation:
        return ModifyReservationOutputModel(
            status="error",
            message=f"Modification failed. Reservation {input_data.reservation_id} not found.",
        )

    if reservation.user_id != input_data.user_id:
        return ModifyReservationOutputModel(
            status="error",
            message="Modification failed. You are not authorized to modify this reservation.",
        )

    if reservation.status != "Active":
        return ModifyReservationOutputModel(
            status="error",
            message="Modification failed. Only Active reservations can be modified.",
        )

    if input_data.new_number_guests is not None:
        reservation.number_guests = input_data.new_number_guests

    if input_data.new_price_per_person is not None:
        reservation.price_per_person = input_data.new_price_per_person

    if input_data.new_reservation_date is not None:
        reservation.reservation_date = input_data.new_reservation_date

    if input_data.new_reservation_time is not None:
        reservation.reservation_time = input_data.new_reservation_time

    if input_data.upgrade_private_dining and not reservation.has_private_dining:
        reservation.has_private_dining = True

    new_charge = round(reservation.price_per_person * reservation.number_guests, 2)
    if reservation.has_private_dining:
        new_charge = round(new_charge + PRIVATE_DINING_UPGRADE_FEE, 2)
    reservation.reservation_charge = new_charge

    global_reservations_db.update_reservation(
        input_data.reservation_id,
        number_guests=reservation.number_guests,
        price_per_person=reservation.price_per_person,
        reservation_date=reservation.reservation_date,
        reservation_time=reservation.reservation_time,
        has_private_dining=reservation.has_private_dining,
        reservation_charge=new_charge,
    )

    private_note = " (private dining active)" if reservation.has_private_dining else ""
    return ModifyReservationOutputModel(
        status="success",
        message=f"Reservation {input_data.reservation_id} successfully modified. New total charge: ${new_charge:.2f}{private_note}.",
        reservation_id=input_data.reservation_id,
        reservation_date=reservation.reservation_date,
        reservation_time=reservation.reservation_time,
        new_charge=new_charge,
        has_private_dining=reservation.has_private_dining,
    )
