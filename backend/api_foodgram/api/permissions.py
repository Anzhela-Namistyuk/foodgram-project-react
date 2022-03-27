from rest_framework import permissions


class ReadAndOwner(permissions.BasePermission):
    """Класс пермишена для доступа к изменению контента,
    генерируемого пользователями. Такой контент могут изменять
    только авторы.
    """

    def has_permission(self, request, view):
        """Метод проверяет тип запроса.
        На чтение - доступно любому пользователю.
        На изменение  - доступно только автору.
        """
        return (request.method in permissions.SAFE_METHODS
                or request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        """Метод проверяет является метод безопасным или
        пользователь это автор.
        """
        return (request.method in permissions.SAFE_METHODS
                or obj.author == request.user)
