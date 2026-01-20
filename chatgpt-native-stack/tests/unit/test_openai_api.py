"""
Unit tests for OpenAI API integration (content generation).
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))


@pytest.mark.unit
def test_openai_client_initialization(mock_openai_client):
    """Test OpenAI client initializes correctly."""
    assert mock_openai_client is not None
    assert hasattr(mock_openai_client, 'chat')


@pytest.mark.unit
def test_email_generation_with_mock(mock_openai_response, mock_openai_client):
    """Test email generation with mocked API."""
    # Import path fix
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../content-generation'))
    from generate_emails import generate_email
    
    # Mock the client
    with patch('content_generation.generate_emails.OpenAI') as mock_client_class:
        mock_client_class.return_value = mock_openai_client
        
        # Mock response
        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock()]
        mock_completion.choices[0].message.content = mock_openai_response['choices'][0]['message']['content']
        mock_openai_client.chat.completions.create.return_value = mock_completion
        
        # Test
        result = generate_email(mock_openai_client, 'medical', 1)
        
        # Assert
        assert result is not None
        assert 'subject_a' in result
        assert 'subject_b' in result
        assert 'body' in result
        assert 'Test Subject A' in result['subject_a']


@pytest.mark.unit
def test_landing_page_generation_with_mock(mock_openai_client):
    """Test landing page generation with mocked API."""
    from content_generation.generate_landing_pages import generate_landing_page
    
    # Mock response
    mock_content = "# Test Landing Page\n## Test Subheading\nTest content"
    mock_completion = MagicMock()
    mock_completion.choices = [MagicMock()]
    mock_completion.choices[0].message.content = mock_content
    mock_openai_client.chat.completions.create.return_value = mock_completion
    
    # Test
    result = generate_landing_page(mock_openai_client, 'medical', 'A')
    
    # Assert
    assert result is not None
    assert '# Test Landing Page' in result


@pytest.mark.unit
def test_email_content_parsing():
    """Test parsing of email content."""
    content = """SUBJECT_A: Test Subject A
SUBJECT_B: Test Subject B

BODY:
This is the email body.
It has multiple lines.

Best regards,
Alex"""
    
    lines = content.strip().split('\n')
    subject_a = ""
    subject_b = ""
    body_lines = []
    in_body = False
    
    for line in lines:
        if line.startswith("SUBJECT_A:"):
            subject_a = line.replace("SUBJECT_A:", "").strip()
        elif line.startswith("SUBJECT_B:"):
            subject_b = line.replace("SUBJECT_B:", "").strip()
        elif line.startswith("BODY:"):
            in_body = True
        elif in_body:
            body_lines.append(line)
    
    body = '\n'.join(body_lines).strip()
    
    assert subject_a == "Test Subject A"
    assert subject_b == "Test Subject B"
    assert "This is the email body" in body
    assert "Best regards" in body


@pytest.mark.unit
def test_vertical_definitions(test_verticals):
    """Test vertical definitions are valid."""
    assert 'medical' in test_verticals
    assert 'legal' in test_verticals
    
    for vertical, data in test_verticals.items():
        assert 'name' in data
        assert 'targets' in data
        assert 'stat' in data


@pytest.mark.unit
def test_email_personalization_tokens(sample_email_content):
    """Test email contains personalization tokens."""
    assert '{{firstname}}' in sample_email_content
    assert '{{company}}' in sample_email_content
    assert '{{city}}' in sample_email_content


@pytest.mark.unit
@patch('builtins.open', create=True)
def test_save_email_content(mock_open):
    """Test saving email content to file."""
    from content_generation.generate_emails import save_email
    
    email_data = {
        'subject_a': 'Subject A',
        'subject_b': 'Subject B',
        'body': 'Email body'
    }
    
    # Mock file write
    mock_file = MagicMock()
    mock_open.return_value.__enter__.return_value = mock_file
    
    with patch('os.makedirs'):
        result = save_email('medical', 1, email_data)
    
    # File should be written
    assert mock_file.write.called


@pytest.mark.unit
def test_openai_api_error_handling(mock_openai_client):
    """Test OpenAI API error handling."""
    from content_generation.generate_emails import generate_email
    
    # Mock API error
    mock_openai_client.chat.completions.create.side_effect = Exception("API Error")
    
    # Should handle error gracefully
    result = generate_email(mock_openai_client, 'medical', 1)
    
    assert result is None


@pytest.mark.integration
@pytest.mark.skipif(not os.getenv('OPENAI_API_KEY'), reason="OPENAI_API_KEY not set")
def test_real_email_generation():
    """Test real email generation (uses API credit)."""
    from openai import OpenAI
    from content_generation.generate_emails import generate_email
    
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    # Generate one real email
    result = generate_email(client, 'medical', 1)
    
    # Assert
    assert result is not None
    assert 'subject_a' in result
    assert len(result['subject_a']) > 0
    assert 'body' in result
    assert len(result['body']) > 50  # Should be substantial


@pytest.mark.integration
@pytest.mark.skipif(not os.getenv('OPENAI_API_KEY'), reason="OPENAI_API_KEY not set")
def test_real_landing_page_generation():
    """Test real landing page generation (uses API credit)."""
    from openai import OpenAI
    from content_generation.generate_landing_pages import generate_landing_page
    
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    # Generate one real landing page
    result = generate_landing_page(client, 'medical', 'A')
    
    # Assert
    assert result is not None
    assert len(result) > 200  # Should be substantial
    assert '#' in result  # Should have markdown headers

