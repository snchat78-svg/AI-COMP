from __future__ import annotations

import hmac
import json
import logging
import os
from collections.abc import Mapping
from typing import Literal
import time
from http import HTTPStatus
from urllib.parse import parse_qs
from uuid import uuid4

from fastapi import APIRouter, Request
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from ai_comp.analysis.personalized_preparation import PersonalizedPreparationService
from ai_comp.application.adaptive_practice_recommendations import (