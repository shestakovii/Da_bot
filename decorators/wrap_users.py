from functools import wraps



def convert_tg_id_to_user_id(func):
    """
    Декоратор для автоматической конвертации tg_user_id во внутренний userId.
    Обрабатывает как позиционные(args), так и именованные (kwargs) аргументы.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Ищем tg_user_id в kwargs
        if 'tg_user_id' in kwargs:
            kwargs['user_id'] = db_get_user_id_by_tg_id(kwargs['tg_user_id'])
            del kwargs['tg_user_id']
        # Ищем tg_user_id в args (если он передан как позиционный аргумент)
        else:
            # Предполагаем, что tg_user_id — это первый позиционный аргумент
            if args and isinstance(args[0], int):  # Проверяем, что первый аргумент — это tg_user_id
                user_id = db_get_user_id_by_tg_id(args[0])
                args = (user_id,) + args[1:]  # Заменяем tg_user_id на user_id
        return func(*args, **kwargs)
    return wrapper