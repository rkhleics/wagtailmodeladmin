from django.utils.six.moves.urllib.parse import urlparse
from django.http import HttpResponseRedirect
from django.core.urlresolvers import resolve, Resolver404


class ModelAdminMiddleware(object):
    """
    Whenever loading wagtail's wagtailadmin_explore url, we check the session
    for a 'return_to_list_url' value (set by some views), to see if the user
    should be redirected to a custom list view instead, and if so, redirect
    them to it.
    """

    def process_request(self, request):
        """
        Ignore unnecessary actions for static file requests, posts, or ajax
        requests. We're only interested in redirecting following a 'natural'
        request redirection within the admin area.
        """
        if all([
            request.path.startswith('/admin/'),
            request.method == 'GET',
            not request.is_ajax()
        ]):
            referer_url = request.META.get('HTTP_REFERER')
            return_to_index_url = request.session.get('return_to_index_url')

            try:
                """
                We only want to redirect if we're on the 'wagtailadmin_explore'
                url, and we have something to redirect to.
                """
                resolver_match = resolve(request.path)
                if all((
                    resolver_match.url_name == 'wagtailadmin_explore',
                    return_to_index_url,
                    referer_url)
                ):
                    referer_match = resolve(urlparse(referer_url).path)
                    referer_name = referer_match.url_name
                    referer_ns = referer_match.namespace

                    perform_redirection = False
                    if all([
                        referer_ns == 'wagtailadmin_pages',
                        referer_name in ('add', 'edit', 'delete', 'unpublish',
                                         'copy'),
                    ]):
                        perform_redirection = True
                    elif all([
                        not referer_ns,
                        referer_name in (
                            'wagtailadmin_pages_create',
                            'wagtailadmin_pages_edit',
                            'wagtailadmin_pages_delete',
                            'wagtailadmin_pages_unpublish'
                        ),
                    ]):
                        perform_redirection = True
                    if perform_redirection:
                        del request.session['return_to_index_url']
                        return HttpResponseRedirect(return_to_index_url)

            except Resolver404:
                pass

        return None
