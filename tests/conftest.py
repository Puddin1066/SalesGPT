import os
import sys
from unittest.mock import MagicMock

import pytest
from dotenv import load_dotenv


# Note: Langchain mocking disabled - all dependencies are installed
# If you need mocking for tests without dependencies, uncomment the code below


@pytest.fixture
def load_env():
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_data")
    load_dotenv(dotenv_path=f"{data_dir}/.env")
