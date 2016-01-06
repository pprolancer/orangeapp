from flask import flash


def get_or_create(session, model, commit=True, created_flag=False, **kwargs):
    instance = session.query(model).filter_by(**kwargs).first()
    created = False
    if not instance:
        instance = model(**kwargs)
        session.add(instance)
        if commit:
            session.commit()
        created = True

    return (instance, created) if created_flag else instance


FLASH_ERROR_CATEGORY = 'error'
FLASH_WARNING_CATEGORY = 'warning'


def flash_error(message):
    return flash(message, category=FLASH_ERROR_CATEGORY)


def flash_warning(message):
    return flash(message, category=FLASH_WARNING_CATEGORY)
