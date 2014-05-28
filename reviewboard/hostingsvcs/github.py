import re
from reviewboard.hostingsvcs.repository import HostingServiceRepository
    NEXT_LINK_RE = re.compile(r'\<(?P<link>.+)\>(?=; rel="next")')

    def api_get(self, url, return_headers=False, *args, **kwargs):
        """Performs an HTTP GET to the GitHub API and returns the results.

        If `return_headers` is True, then the result of each call (or
        each generated set of data, if using pagination) will be a tuple
        of (data, headers). Otherwise, the result will just be the data.
        """

            if return_headers:
                return data, headers
            else:
                return data
    def api_get_list(self, url, return_headers=False, *args, **kwargs):
        """Performs an HTTP GET to a GitHub list API and yields the results.

        This will follow all "next" links provided by the API, yielding each
        page of data. In this case, it works as a generator.

        If `return_headers` is True, then each page of results will be
        yielded as a tuple of (data, headers). Otherwise, just the data
        will be yielded.
        """
        while url:
            data, headers = self.api_get(url, return_headers=True,
                                         *args, **kwargs)

            if return_headers:
                yield data, headers
            else:
                yield data

            url = self._get_next_link(headers)

    def api_get_remote_repositories(self, api_url, owner, plan):
        url = api_url

        if plan.endswith('org'):
            url += 'orgs/%s/repos' % owner
        elif owner == self.account.username:
            # All repositories belonging to an authenticated user.
            url += 'user/repos'
        else:
            # Only public repositories for the user.
            url += 'users/%s/repos?type=all' % owner

        for data in self.api_get_list(self._build_api_url(url)):
            for repo_data in data:
                yield repo_data

        url = '/'.join(api_paths)

        if '?' in url:
            url += '&'
        else:
            url += '?'

        url += 'access_token=%s' % self.account.data['authorization']['token']

        return url

    def _get_next_link(self, headers):
        """Return the next link extracted from the Links in headers.

        This is used to traverse a paginated response by one of the
        API pagination functions.
        """
        try:
            links = headers.get('Link')
            return self.NEXT_LINK_RE.match(links).group('link')
        except (KeyError, AttributeError, TypeError):
            return None
    def get_remote_repositories(self, owner, plan=None):
        """Return a list of remote repositories matching the given criteria.

        This will look up each remote repository on GitHub that the given
        owner either owns or is a member of.

        If the plan is an organization plan, then `owner` is expected to be
        an organization name, and the resulting repositories with be ones
        either owned by that organization or that the organization is a member
        of, and can be accessed by the authenticated user.

        If the plan is a public or private plan, and `owner` is the current
        user, then that user's public and private repositories or ones
        they're a member of will be returned.

        Otherwise, `owner` is assumed to be another GitHub user, and their
        accessible repositories that they own or are a member of will be
        returned.
        """
        if plan not in ('public', 'private', 'public-org', 'private-org'):
            raise InvalidPlanError(plan)

        url = self.get_api_url(self.account.hosting_url)

        for repo in self.client.api_get_remote_repositories(url, owner, plan):
            yield HostingServiceRepository(name=repo['name'],
                                           owner=repo['owner']['login'],
                                           scm_type='Git',
                                           path=repo['url'],
                                           mirror_path=repo['mirror_url'],
                                           extra_data=repo)
