from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from django.db import connection
from django.db import utils
from django.http import Http404
from tenant_schemas.utils import remove_www_and_dev, get_tenant_model, get_public_schema_name
from django.utils.deprecation import MiddlewareMixin


class MultFinalMiddleware(MiddlewareMixin):

    def process_request(self, request):
        connection.set_schema_to_public()
        hostname_without_port = remove_www_and_dev(
            request.get_host().split(':')[0])

        TenantModel = get_tenant_model()

        try:
            request.tenant = TenantModel.objects.get(
                domain_url=hostname_without_port)

        except utils.DatabaseError:
            request.urlconf = settings.PUBLIC_SCHEMA_URLCONF
            return
        except TenantModel.DoesNotExist:
            if hostname_without_port in ("127.0.0.1", "localhost", "multidemo.com"):
                request.urlconf = settings.PUBLIC_SCHEMA_URLCONF
                return
            else:
                raise Http404

        connection.set_tenant(request.tenant)
        ContentType.objects.clear_cache()

        if hasattr(settings, "PUBLIC_SCHEMA_URLCONF") and request.tenant.schema_name == get_public_schema_name():
            request.urlconf = settings.PUBLIC_SCHEMA_URLCONF

        if hasattr(settings, "API_URLCONF") and request.tenant.name == 'API':
            self.urlconf = settings.API_URLCONF