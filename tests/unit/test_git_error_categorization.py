"""Tests for git error categorization system."""

import pytest

from ccg.git import GitErrorCategory, categorize_git_error


class TestGitErrorCategory:
    """Test GitErrorCategory enum."""

    def test_permission_category_has_correct_patterns(self) -> None:
        """Should have permission-related error patterns."""
        patterns = GitErrorCategory.PERMISSION.value

        assert "permission denied" in patterns
        assert "access denied" in patterns
        assert "403 forbidden" in patterns
        assert "401 unauthorized" in patterns

    def test_network_category_has_correct_patterns(self) -> None:
        """Should have network-related error patterns."""
        patterns = GitErrorCategory.NETWORK.value

        assert "ssh: connect to host" in patterns
        assert "connection refused" in patterns
        assert "network unreachable" in patterns
        assert "could not resolve host" in patterns

    def test_authentication_category_has_correct_patterns(self) -> None:
        """Should have authentication-related error patterns."""
        patterns = GitErrorCategory.AUTHENTICATION.value

        assert "authentication failed" in patterns
        assert "terminal prompts disabled" in patterns
        assert "could not read username" in patterns
        assert "invalid credentials" in patterns

    def test_repository_category_has_correct_patterns(self) -> None:
        """Should have repository-related error patterns."""
        patterns = GitErrorCategory.REPOSITORY.value

        assert "not found" in patterns
        assert "fatal: could not read from remote repository" in patterns
        assert "please make sure you have the correct access rights" in patterns


class TestCategorizeGitError:
    """Test categorize_git_error function."""

    # Permission errors
    def test_categorize_permission_denied_publickey(self) -> None:
        """Should categorize 'Permission denied (publickey)' as PERMISSION."""
        error = "Permission denied (publickey)."
        category = categorize_git_error(error)

        assert category == GitErrorCategory.PERMISSION

    def test_categorize_access_denied(self) -> None:
        """Should categorize 'access denied' as PERMISSION."""
        error = "fatal: unable to access 'https://github.com/repo.git/': Access denied"
        category = categorize_git_error(error)

        assert category == GitErrorCategory.PERMISSION

    def test_categorize_403_forbidden(self) -> None:
        """Should categorize '403 forbidden' as PERMISSION."""
        error = "error: The requested URL returned error: 403 Forbidden"
        category = categorize_git_error(error)

        assert category == GitErrorCategory.PERMISSION

    def test_categorize_401_unauthorized(self) -> None:
        """Should categorize '401 unauthorized' as PERMISSION."""
        error = "error: The requested URL returned error: 401 Unauthorized"
        category = categorize_git_error(error)

        assert category == GitErrorCategory.PERMISSION

    # Network errors
    def test_categorize_ssh_connect_to_host(self) -> None:
        """Should categorize SSH connection errors as NETWORK."""
        error = "ssh: connect to host github.com port 22: Connection refused"
        category = categorize_git_error(error)

        assert category == GitErrorCategory.NETWORK

    def test_categorize_connection_refused(self) -> None:
        """Should categorize 'connection refused' as NETWORK."""
        error = "fatal: unable to connect to github.com: Connection refused"
        category = categorize_git_error(error)

        assert category == GitErrorCategory.NETWORK

    def test_categorize_network_unreachable(self) -> None:
        """Should categorize 'network unreachable' as NETWORK."""
        error = "fatal: unable to access repository: Network unreachable"
        category = categorize_git_error(error)

        assert category == GitErrorCategory.NETWORK

    def test_categorize_could_not_resolve_host(self) -> None:
        """Should categorize 'could not resolve host' as NETWORK."""
        error = "fatal: Could not resolve host: github.com"
        category = categorize_git_error(error)

        assert category == GitErrorCategory.NETWORK

    # Authentication errors
    def test_categorize_authentication_failed(self) -> None:
        """Should categorize 'authentication failed' as AUTHENTICATION."""
        error = "fatal: Authentication failed for 'https://github.com/repo.git/'"
        category = categorize_git_error(error)

        assert category == GitErrorCategory.AUTHENTICATION

    def test_categorize_terminal_prompts_disabled(self) -> None:
        """Should categorize 'terminal prompts disabled' as AUTHENTICATION."""
        error = "fatal: could not read Username: terminal prompts disabled"
        category = categorize_git_error(error)

        assert category == GitErrorCategory.AUTHENTICATION

    def test_categorize_could_not_read_username(self) -> None:
        """Should categorize 'could not read username' as AUTHENTICATION."""
        error = "fatal: could not read Username for 'https://github.com'"
        category = categorize_git_error(error)

        assert category == GitErrorCategory.AUTHENTICATION

    def test_categorize_invalid_credentials(self) -> None:
        """Should categorize 'invalid credentials' as AUTHENTICATION."""
        error = "fatal: Invalid credentials provided"
        category = categorize_git_error(error)

        assert category == GitErrorCategory.AUTHENTICATION

    # Repository errors
    def test_categorize_repository_not_found(self) -> None:
        """Should categorize 'repository not found' as REPOSITORY."""
        error = "fatal: repository 'https://github.com/user/repo.git/' not found"
        category = categorize_git_error(error)

        assert category == GitErrorCategory.REPOSITORY

    def test_categorize_could_not_read_from_remote(self) -> None:
        """Should categorize 'could not read from remote repository' as REPOSITORY."""
        error = "fatal: could not read from remote repository."
        category = categorize_git_error(error)

        assert category == GitErrorCategory.REPOSITORY

    def test_categorize_correct_access_rights(self) -> None:
        """Should categorize access rights message as REPOSITORY."""
        error = "Please make sure you have the correct access rights and the repository exists."
        category = categorize_git_error(error)

        assert category == GitErrorCategory.REPOSITORY

    # Edge cases
    def test_categorize_unknown_error_returns_none(self) -> None:
        """Should return None for unrecognized errors."""
        error = "Some completely unknown git error message"
        category = categorize_git_error(error)

        assert category is None

    def test_categorize_empty_string_returns_none(self) -> None:
        """Should return None for empty string."""
        error = ""
        category = categorize_git_error(error)

        assert category is None

    def test_categorize_case_insensitive(self) -> None:
        """Should match patterns case-insensitively."""
        # Uppercase
        error_upper = "PERMISSION DENIED (publickey)"
        category_upper = categorize_git_error(error_upper)
        assert category_upper == GitErrorCategory.PERMISSION

        # Mixed case
        error_mixed = "PeRmIsSiOn DeNiEd"
        category_mixed = categorize_git_error(error_mixed)
        assert category_mixed == GitErrorCategory.PERMISSION

        # Lowercase
        error_lower = "permission denied"
        category_lower = categorize_git_error(error_lower)
        assert category_lower == GitErrorCategory.PERMISSION

    def test_categorize_partial_match(self) -> None:
        """Should match patterns within larger error messages."""
        error = """
        fatal: unable to access 'https://github.com/repo.git/':
        The requested URL returned error: 403 Forbidden while accessing...
        Additional context information here.
        """
        category = categorize_git_error(error)

        assert category == GitErrorCategory.PERMISSION

    def test_categorize_returns_first_matching_category(self) -> None:
        """Should return first matching category when multiple patterns match."""
        # This error contains patterns from both PERMISSION and REPOSITORY categories
        error = "permission denied: repository not found"

        category = categorize_git_error(error)

        # Should return PERMISSION as it's checked first (enum order)
        assert category == GitErrorCategory.PERMISSION


class TestCategorizeGitErrorRealWorldExamples:
    """Test categorization with real-world git error messages."""

    def test_github_ssh_permission_denied(self) -> None:
        """Should categorize GitHub SSH permission denied error."""
        error = """
        git@github.com: Permission denied (publickey).
        fatal: Could not read from remote repository.

        Please make sure you have the correct access rights
        and the repository exists.
        """
        category = categorize_git_error(error)

        assert category == GitErrorCategory.PERMISSION

    def test_github_https_404_not_found(self) -> None:
        """Should categorize GitHub HTTPS 404 error."""
        error = """
        remote: Repository not found.
        fatal: repository 'https://github.com/user/nonexistent.git/' not found
        """
        category = categorize_git_error(error)

        assert category == GitErrorCategory.REPOSITORY

    def test_gitlab_authentication_failed(self) -> None:
        """Should categorize GitLab authentication error."""
        error = """
        remote: HTTP Basic: Access denied
        fatal: Authentication failed for 'https://gitlab.com/repo.git/'
        """
        category = categorize_git_error(error)

        # "Access denied" matches PERMISSION category first
        assert category == GitErrorCategory.PERMISSION

    def test_network_timeout_ssh(self) -> None:
        """Should categorize SSH network timeout."""
        error = """
        ssh: connect to host bitbucket.org port 22: Connection timed out
        fatal: Could not read from remote repository.
        """
        category = categorize_git_error(error)

        assert category == GitErrorCategory.NETWORK

    def test_dns_resolution_failure(self) -> None:
        """Should categorize DNS resolution failure."""
        error = """
        fatal: unable to access 'https://invalid-host.com/repo.git/':
        Could not resolve host: invalid-host.com
        """
        category = categorize_git_error(error)

        assert category == GitErrorCategory.NETWORK

    def test_terminal_prompts_disabled_error(self) -> None:
        """Should categorize terminal prompts disabled error."""
        error = """
        fatal: could not read Username for 'https://github.com': terminal prompts disabled
        """
        category = categorize_git_error(error)

        assert category == GitErrorCategory.AUTHENTICATION
