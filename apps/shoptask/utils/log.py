from utils.generals import get_model

from django_currentuser.middleware import (
    get_current_user, get_current_authenticated_user)


class CreateChangeLog:
    def __init__(self, obj, obj_id, column, old_value, new_value):
        self.model_name = model_name
        self.obj = obj
        self.obj_id = obj_id
        self.column = column
        self.changed_by = get_current_authenticated_user()
        self.old_value = old_value
        self.new_value = new_value

    def save(self):
        from django.contrib.contenttypes.models import ContentType
        ChangeLog = get_model('shoptask', 'ChangeLog')

        ct = ContentType.objects.get_for_model(self.obj, for_concrete_model=False)
        obj = ChangeLog.objects.create(content_type=ct, object_id=self.obj_id,
                                       column=self.column, old_value=self.old_value,
                                       new_value=self.new_value)
        obj.save()
        obj.refresh_from_db()
        return obj
