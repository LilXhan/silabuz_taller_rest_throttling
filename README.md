# Taller

Para nuestro taller haremos uso de Throttling dentro de DRF, para recordar Throttling funciona de forma similar a los permisos, ya que esta determina si la solicitud debe autorizarse y es utilizado para controlar la tasa de solicitudes que los clientes pueden realizar a una API.

Recordar que todos los archivos y código utilizados son del repositorio [DRF](https://github.com/silabuzinc/DRF).

## Aceleración

Podemos definir la velocidad que van a tener las request realizadas. Por lo que, podemos definir una velocidad baja a las request no autenticada y una mucho mayor a los que si cuenten con autenticación.

Antes de ejecutar el cuerpo principal de la vista, se comprueba cada acelerador de la lista. Si alguna comprobación del acelerador falla, se producirán excepciones. Se generará una exceptions.Throttled regulada y el cuerpo principal de la vista no se ejecutará.

Para añadir la política de limitación de forma global, necesitamos modificar nuestro `settings.py`, haciendo uso de `DEFAULT_THROTTLE_CLASSES` y `DEFAULT_THROTTLE_RATES`.

```py
REST_FRAMEWORK = {
    # ...
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/day',
        'user': '1000/day'
    }
}
```

Las descripciones de velocidad utilizadas en `DEFAULT_THROTTLE_RATES`, pueden incluir `second`, `minute`, `hour` o `day` como el periodo de aceleración.

También podemos añadir la política de limitación por vista o por conjunto de vistas. La implementación es soportada por todo tipo de vista que haga uso de `APIView`.

Por ejemplo, dentro de nuestro `versionedTodo/v4/api.py`, tenemos la siguiente vista:

```py
from todos.models import Todo
from .serializers import TodoSerializer
from rest_framework import status
from rest_framework.response import Response
from .pagination import StandardResultsSetPagination
from rest_framework import viewsets, filters 

class TodoViewSet(viewsets.ModelViewSet):
    queryset = Todo.objects.all()
    serializer_class = TodoSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]

    search_fields = ['title', 'body']
    ordering = ('-id')
```

Por lo que, podemos añadir nuestra política de limitación.

```py
from todos.models import Todo
from .serializers import TodoSerializer
from rest_framework import status
from rest_framework.response import Response
from .pagination import StandardResultsSetPagination
from rest_framework import viewsets, filters

# Añadimos UserRateThrottle
from rest_framework.throttling import UserRateThrottle

class TodoViewSet(viewsets.ModelViewSet):
    queryset = Todo.objects.all()
    serializer_class = TodoSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]

    search_fields = ['title', 'body']
    ordering = ('-id')

    # Definición de la clase
    throttle_classes = [UserRateThrottle]
```

De la misma forma, podemos añadir las limitaciones a las rutas que podemos crearlas con el decorador `@action`(más información [aquí](https://www.django-rest-framework.org/api-guide/viewsets/#marking-extra-actions-for-routing)). Las clases de aceleración establecidas de esta forma anularán cualquier configuración de la clase al nivel de conjunto de vistas.

```py
@action(detail=True, methods=["post"], throttle_classes=[UserRateThrottle])
def example_adhoc_method(request, pk=None):
    content = {
        'status': 'request was permitted'
    }
    return Response(content)
```

## Caché

Las clases de acelerador que proporciona DRF usan el backend de caché de Django. Se debe estar seguro que se ah realizado la configuración de caché. Esto ya lo hemos revisado anteriormente. Pero para este proyecto haremos uso de `LocMemCache`, el cual viene por defecto y que sirve para configuraciones simples como esta.

Para añadirlo, añadiremos lo siguiente `settings.py`.

```py
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    },
}
```

Entonces, no necesitamos modificar nada más dentro del Throttling.

Pero, si hacemos uso de otro cache, necesitamos crear una clase Throttling específica que haga uso de este, un ejemplo de este tipo de clase es el siguiente:

```py
from django.core.cache import caches

class CustomAnonRateThrottle(AnonRateThrottle):
    cache = caches['alternate']
```

> Cabe resalta que al crear una clase de este tipo, también se debe realizar el cambio del tipo de Trottle en nuestro `settings.py` haciendo referencia a la nueva clase creada.

## Añadiendo el Throttling apropiado para nuestro proyecto

Para nuestro proyecto, haremos uso del `ScopedRateThrottle` en cual va a restringir el acceso a parte específicas de la API. Este acelerador solo se aplicará si la vista a la que accede cuenta con una propiedad llamada `throttle_scope`. En la cual crearemos una clave que será utilizada para definir la limitación correspondiente a la vista.

Dentro de nuestro `versionedTodo/v4/api.py`, modificaremos la política de limitación.

```py
from todos.models import Todo
from .serializers import TodoSerializer
from rest_framework import status
from rest_framework.response import Response
from .pagination import StandardResultsSetPagination
from rest_framework import viewsets, filters 

class TodoViewSet(viewsets.ModelViewSet):
    queryset = Todo.objects.all()
    serializer_class = TodoSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]

    search_fields = ['title', 'body']
    ordering = ('-id')

    # Definición de la clave
    throttle_scope = 'get'
```

Únicamente definimos el `scope` dentro de nuestra vista. Dentro de `settings.py` haremos la modificación del Throttling.

```py
REST_FRAMEWORK = {
    # ...
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.ScopedRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'get': '1/day'
    }
}
```

Para hacer la prueba definimos que únicamente se pueda hacer un request a nuestra vista. Por lo que si accedemos a la ruta `http://127.0.0.1:8000/api/v4/todo/` y actualizamos 2 veces, deberíamos obtener la siguiente respuesta.

![No más accesos a la API](https://photos.silabuz.com/uploads/big/dc8bbbcdd4b3bb6c5e14db24f3977683.PNG)

## Throttles personalizados

Podemos crear un acelerador personalizado, haciendo uso de la clase base `BaseThrottle` implementando `allow_request(self, request, view)`. El método debe devolver True si se debe permitir la solicitud, y False de lo contrario.

Opcionalmente, también puede anular el método `wait()` . Si se implementa, `wait()` debería devolver un número recomendado de segundos para esperar antes de intentar la siguiente solicitud, o `None` . El método `wait()` solo se llamará si `allow_request()` ha devuelto `False` anteriormente.

Si se implementa el método `wait()` y la solicitud se limita, entonces se incluirá un encabezado Retry-After en la respuesta.

### Ejemplo de un Throttle personalizado

Por ejemplo, podemos crear un acelerador, que acelerará aleatoriamente 1 de cada 10 solicitudes.

```py
import random

class RandomRateThrottle(throttling.BaseThrottle):
    def allow_request(self, request, view):
        return random.randint(1, 10) != 1
```

Si te interesa conocer más acerca del Throttling puedes obtener más información [aquí](https://github.com/encode/django-rest-framework/blob/master/rest_framework/throttling.py).

## Tarea

Posterior a la implementación y prueba del `ScopedRateThrottle`, nuestra última tarea de la unidad será la siguiente.

### API de pagos

Esta api funcionará como un pequeño proyecto, en la cual deben hacer uso de las siguientes tecnologías.

-   simpleJWT
    
-   Throttling
    

Para esta API de pagos el enunciado es el siguiente.

Se necesitará crear una aplicación de usuarios que permita el login como lo vimos anteriormente. Luego de esto, crear una aplicación pagos la cual debe registrar el usuario, el servicio, el monto, y la fecha de pago.

La aplicación de pagos solo debe admitir las siguiente operaciones:

-   GET (list y retrieve)
    
-   POST
    

Debe contener paginación y filtros de búsqueda para los campos de `user__id`, `fecha_pago` y `servicio`.

Los servicios a usar dentro de la APP para registrar los pagos son lo siguientes:

-   Netflix
    
-   Amazon Video
    
-   Star +
    
-   Paramount +
    

Recordar que esta aplicación y las vistas creadas, deben hacer uso de simpleJWT para que se haga uso del login de los usuarios.

Por último, la creación de pagos debe estar limitada a 1000 request por día.

## Otras herramientas

Dentro del mundo de desarrollo existen diversas herramientas y tecnologías a utilizar, algunas que les recomendamos que aprendan para su crecimiento son las siguientes.

-   [Cloudfare](https://www.cloudflare.com/): Va relaciondo con Throttling
    
-   [SonarCloud](https://www.sonarsource.com/): Herramienta para calcular la calidad de nuestro código (errores, bugs, codesmells, etc.).
    
-   [Jenkins](https://www.jenkins.io/): Jenkins es un servidor open source para la integración continua. Es una herramienta que se utiliza para compilar y probar proyectos de software de forma continua, lo que facilita a los desarrolladores integrar cambios en un proyecto y entregar nuevas versiones a los usuarios.

Links:

 - [Slide](https://docs.google.com/presentation/d/e/2PACX-1vQzrDDqUpQEqtpFaovYh1fSa3itO3yZCYIP6CJIv5JUr0ZZMUwlD5tEMkSvy8600l4i-AlZGxL5ebLJ/embed?start=false&loop=false&delayms=3000)

Videos:
 - [Teoria](https://www.youtube.com/watch?v=l0jqM8Q_kV8&list=PLxI5H7lUXWhgHbHF4bNrZdBHDtf0CbEeH&index=17&t=1s)
 - [Practica](https://www.youtube.com/watch?v=-RwR0tTl8J8&list=PLxI5H7lUXWhgHbHF4bNrZdBHDtf0CbEeH&index=18)