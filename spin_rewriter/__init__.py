import simplejson as json
from collections import namedtuple
from spin_rewriter import exceptions as ex
from configparser import ConfigParser
import requests
import re
import json
import string


class Api(object):
    """A class representing the Spin Rewriter API
    (http://www.spinrewriter.com/).
    """
    URL = 'http://www.spinrewriter.com/action/api'
    """URL for invoking the API"""

    _tmp_list = ['api_quota', 'text_with_spintax', 'unique_variation',
                 'unique_variation_from_spintax']
    ACTION = namedtuple('ACTION', _tmp_list)(*_tmp_list)
    """collection of possible values for the action parameter"""

    _tmp_list = ['low', 'medium', 'high']
    CONFIDENCE_LVL = namedtuple('CONFIDENCE_LVL', ['low', 'medium', 'high'])(
        *_tmp_list)
    """collection of possible values for the confidence_level parameter"""

    SPINTAX_FORMAT = namedtuple(
        'SPINTAX_FORMAT',
        ['pipe_curly', 'tilde_curly', 'pipe_square', 'spin_tag']
    )(*['{|}', '{~}', '[|]', '[spin]'])
    """collection of possible values for the spintax_format parameter"""

    _tmp_list = ['email_address', 'api_key',
                 'action', 'text', 'protected_terms',
                 'confidence_level', 'nested_spintax', 'spintax_format']
    REQ_P_NAMES = namedtuple('REQ_P_NAMES', _tmp_list)(*_tmp_list)
    """collection of all request parameters' names"""

    _tmp_list = ['status', 'response', 'api_requests_made',
                 'api_requests_available', 'protected_terms',
                 'confidence_level']
    RESP_P_NAMES = namedtuple('RESP_P_NAMES', _tmp_list)(*_tmp_list)
    """collection of all response fields' names"""

    _tmp_list = ['ok', 'error']
    STATUS = namedtuple('STATUS', ['ok', 'error'])(
        *map(lambda x: x.upper(), _tmp_list))
    """possible response status strings returned by API"""

    def __init__(self, email_address, api_key):
        self.email_address = email_address
        self.api_key = api_key

    def api_quota(self):
        """Return the number of made and remaining API calls for the 24-hour
        period.
        :return: remaining API quota
        :rtype: dictionary
        """
        params = (
            (self.REQ_P_NAMES.email_address, self.email_address),
            (self.REQ_P_NAMES.api_key, self.api_key),
            (self.REQ_P_NAMES.action, self.ACTION.api_quota),
        )
        response = self._send_request(params)
        return response

    def text_with_spintax(self, text, protected_terms=None,
                          confidence_level=CONFIDENCE_LVL.medium,
                          nested_spintax=False,
                          spintax_format=SPINTAX_FORMAT.pipe_curly):
        """Return processed spun text with spintax.
        :param text: original text that needs to be changed
        :type text: string
        :param protected_terms: (optional) keywords and key phrases that
            should be left intact
        :type protected_terms: list of strings
        :param confidence_level: (optional) the confidence level of
            the One-Click Rewrite process
        :type confidence_level: string
        :param nested_spintax: (optional) whether or not to also spin
            single words inside already spun phrases
        :type nested_spintax: boolean
        :param spintax_format: (optional) spintax format to use in
            returned text
        :type spintax_format: string
        :return: processed text and some other meta info
        :rtype: dictionary
        """
        response = self._transform_plain_text(
            self.ACTION.text_with_spintax,
            text,
            protected_terms,
            confidence_level,
            nested_spintax,
            spintax_format
        )

        if response[self.RESP_P_NAMES.status] == self.STATUS.error:
            self._raise_error(response)
        else:
            return response

    def unique_variation(
            self,
            text,
            protected_terms=None,
            confidence_level=CONFIDENCE_LVL.medium,
            nested_spintax=False,
            spintax_format=SPINTAX_FORMAT.pipe_curly
    ):
        """Return a unique variation of the given text.
        :param text: original text that needs to be changed
        :type text: string
        :param protected_terms: (optional) keywords and key phrases that
            should be left intact
        :type protected_terms: list of strings
        :param confidence_level: (optional) the confidence level of
            the One-Click Rewrite process
        :type confidence_level: string
        :param nested_spintax: (optional) whether or not to also spin
            single words inside already spun phrases
        :type nested_spintax: boolean
        :param spintax_format: (optional) (probably not relevant here?
            But API documentation not clear here ...)
        :type spintax_format: string
        :return: processed text and some other meta info
        :rtype: dictionary
        """
        response = self._transform_plain_text(
            self.ACTION.unique_variation, text, protected_terms,
            confidence_level, nested_spintax, spintax_format
        )

        if response[self.RESP_P_NAMES.status] == self.STATUS.error:
            self._raise_error(response)
        else:
            return response

    def unique_variation_from_spintax(
            self,
            text,
            nested_spintax=False,
            spintax_format=SPINTAX_FORMAT.pipe_curly
    ):
        """Return a unique variation of an already spun text.
        :param text: text to process
        :type text: string
        :param nested_spintax: whether or not to also spin single words
            inside already spun phrases
        :type nested_spintax: boolean
        :param spintax_format: (probably not relevant here?
            But API documentation not clear here ...)
        :type spintax_format: string
        :return: processed text and some other meta info
        :rtype: dictionary
        """
        params = (
            (self.REQ_P_NAMES.email_address, self.email_address),
            (self.REQ_P_NAMES.api_key, self.api_key),
            (
                self.REQ_P_NAMES.action,
                self.ACTION.unique_variation_from_spintax
            ),
            (self.REQ_P_NAMES.text, text.encode('utf-8')),
            (self.REQ_P_NAMES.nested_spintax, nested_spintax),
            (self.REQ_P_NAMES.spintax_format, spintax_format),
        )
        response = self._send_request(params)

        if response[self.RESP_P_NAMES.status] == self.STATUS.error:
            self._raise_error(response)
        else:
            return response

    def _send_request(self, params):
        """Invoke Spin Rewriter API with given parameters and return its
        response.
        :param params: parameters to pass along with the request
        :type params: tuple of 2-tuples
        :return: API's response (already JSON-decoded)
        :rtype: dictionary
        """
        result = requests.post(self.URL, data=params)
        return json.loads(result.text)

    def _raise_error(self, api_response):
        """Examine the API response and raise exception of the appropriate
        type.
        NOTE: usage of this method only makes sense when API response's
        status indicates an error
        :param api_response: API's response fileds
        :type api_response: dictionary
        """
        error_msg = api_response[self.RESP_P_NAMES.response]

        if (
            re.match(
                r'Authentication failed. '
                r'No user with this email address found.',
                error_msg,
                re.IGNORECASE
            ) or
            re.match(
                r'Authentication failed. '
                r'Unique API key is not valid for this user.',
                error_msg,
                re.IGNORECASE
            ) or
            re.match(
                r'This user does not have a valid Spin Rewriter subscription.',
                error_msg,
                re.IGNORECASE
            )
        ):
            raise ex.AuthenticationError(error_msg)

        elif re.match(
            r'API quota exceeded. '
            r'You can make \d+ requests per day.',
            error_msg,
            re.IGNORECASE
        ):
            raise ex.QuotaLimitError(error_msg)

        elif re.match(
            r'You can only submit entirely new text '
            r'for analysis once every \d+ seconds.',
            error_msg,
            re.IGNORECASE
        ):
            raise ex.UsageFrequencyError(error_msg)

        elif re.match(
            r'Requested action does not exist. '
            r'Please refer to the Spin Rewriter API documentation.',
            error_msg,
            re.IGNORECASE
        ):
            # NOTE: This should never occur unless
            # there is a bug in the API library.
            raise ex.UnknownActionError(error_msg)

        elif re.match(
            r'Email address and unique API key are both required. '
            r'At least one is missing.',
            error_msg,
            re.IGNORECASE
        ):
            # NOTE: This should never occur unless
            # there is a bug in the API library.
            raise ex.MissingParameterError(error_msg)

        elif (
            re.match(
                r'Original text too short.',
                error_msg,
                re.IGNORECASE
            ) or
            re.match(
                r'Original text too long. Text can have up to 4,000 words.',
                error_msg,
                re.IGNORECASE
            ) or
            re.match(
                r'Original text after analysis too long. '
                r'Text can have up to 4,000 words.',
                error_msg,
                re.IGNORECASE
            ) or
            re.match(
                r'Spinning syntax invalid. '
                r'With this action you should provide text with existing valid'
                r'{first option|second option} spintax.',
                error_msg,
                re.IGNORECASE
            ) or
            re.match(
                r'The {first|second} spinning syntax invalid. '
                r'Re-check the syntax, i.e. curly brackets and pipes\.',
                error_msg,
                re.IGNORECASE
            ) or
            re.match(
                r'Spinning syntax invalid.',
                error_msg,
                re.IGNORECASE
            )
        ):
            raise ex.ParamValueError(error_msg)

        elif (
            re.match(
                r'Analysis of your text failed. '
                r'Please inform us about this.',
                error_msg,
                re.IGNORECASE
            ) or
            re.match(
                r'Synonyms for your text could not be loaded. '
                r'Please inform us about this.',
                error_msg,
                re.IGNORECASE
            ) or
            re.match(
                r'Unable to load your new analyzed project.',
                error_msg,
                re.IGNORECASE
            ) or
            re.match(
                r'Unable to load your existing analyzed project.',
                error_msg,
                re.IGNORECASE
            ) or
            re.match(
                r'Unable to find your project in the database.',
                error_msg,
                re.IGNORECASE
            ) or
            re.match(
                r'Unable to load your analyzed project.',
                error_msg,
                re.IGNORECASE
            ) or
            re.match(
                r'One-Click Rewrite failed.',
                error_msg,
                re.IGNORECASE
            )
        ):
            raise ex.InternalApiError(error_msg)

        else:
            raise ex.UnknownApiError(error_msg)

    def _transform_plain_text(
            self,
            action,
            text,
            protected_terms,
            confidence_level,
            nested_spintax,
            spintax_format
    ):
        """Transform plain text using SpinRewriter API.
        Pack parameters into format as expected by the _send_request method and
        invoke the action method to get transformed text from the API.
        :param action: name of the action that will be requested from API
        :type action: string
        :param text: text to process
        :type text: string
        :param protected_terms: keywords and key phrases that should be left
            intact
        :type protected_terms: list of strings
        :param confidence_level: the confidence level of the One-Click Rewrite
            process
        :type confidence_level: string
        :param nested_spintax: whether or not to also spin single words inside
            already spun phrases
        :type nested_spintax: boolean
        :param spintax_format: spintax format to use in returned text
        :type spintax_format: string
        :return: processed text and some other meta info
        :rtype: dictionary
        """
        protected_terms = ' || '

        params = (
            (self.REQ_P_NAMES.email_address, self.email_address),
            (self.REQ_P_NAMES.api_key, self.api_key),
            (self.REQ_P_NAMES.action, action),
            (self.REQ_P_NAMES.text, text.encode('utf-8')),
            (self.REQ_P_NAMES.protected_terms, protected_terms),
            (self.REQ_P_NAMES.confidence_level, confidence_level),
            (self.REQ_P_NAMES.nested_spintax, nested_spintax),
            (self.REQ_P_NAMES.spintax_format, spintax_format),
        )
        return self._send_request(params)


class SpinRewriter(object):
    """A facade for easier usage of the raw Spin Rewriter API."""

    def __init__(self):
        config = ConfigParser()
        config.read('config.ini')
        self.email_address = str(config['SPINREWRITER']['email_address'])
        self.api_key = str(config['SPINREWRITER']['api_key'])
        self.api = Api(self.email_address, self.api_key)

    def unique_variation(
            self, text, confidence_level=Api.CONFIDENCE_LVL.high):
        """Return unique variation of the given text.
        :param text: text to process
        :type text: string
        :param confidence_level: how 'confident' the spinner API is when
            transforming the text
        :type confidence_level: Api.CONFIDENCE_LVL
        :return: spinned version of the original text
        :rtype: string
        """
        response = self.api.unique_variation(text, ' || ', confidence_level)
        return response[Api.RESP_P_NAMES.response]

    def text_with_spintax(
            self, text, confidence_level=Api.CONFIDENCE_LVL.medium):
        """Return text with spintax elements inserted.
        :param text: text to process
        :type text: string
        :param confidence_level: how 'confident' the spinner API is when
            transforming the text
        :type confidence_level: Api.CONFIDENCE_LVL
        :return: original text with spintax elements
        :rtype: string
        """
        response = self.api.text_with_spintax(text, confidence_level)
        return response[Api.RESP_P_NAMES.response]
