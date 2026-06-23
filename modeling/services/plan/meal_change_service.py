def change_meal_menu(meal: dict, new_menu_id: int) -> dict:
    meal["menu_id"] = new_menu_id
    return meal