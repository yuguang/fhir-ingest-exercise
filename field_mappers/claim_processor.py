import json
from field_mappers.base import FHIRResourceProcessor, get_value_at_json_path
import logging
from normalizers.enum_normalizer import GenderNormalizer

LOG = logging.getLogger(__name__)



class FHIRClaimsProcessor(FHIRResourceProcessor):
    def validate_dates(self):
        """
        Validate date fields
        """
        date_fields = ["billablePeriod.start", "billablePeriod.end"]
        datetime_fields = ["created"]
        for field in date_fields:
            self.validate_date_string(self.data, field)
        for field in datetime_fields:
            self.validate_datetime_string(self.data, field)

    def validate(self):
        """
        Validate the claims data.

        Implement validations such as checking required fields,
        validating date formats, ensuring identifiers meet expected patterns, etc.
        """
        required_fields = ['billablePeriod', 'contained', 'created', 'diagnosis', 'id',
                           'patient', 'provider', 'resourceType', 'status', 'total', 'type', 'use']
        for field in required_fields:
            if field not in self.data:
                LOG.warning(f"Missing required field: {field}")
        self.validate_dates()

        # patient ID may be missing and come in later in some cases
        if "patient" not in self.data:
            LOG.info("Patient data is missing.")
        elif "id" not in self.data:
            LOG.warning("Claim ID is missing.")


    def map_values(self):
        """
        Maps to structured zone table
        Note: due to time constraints not all fields are included
        """
        mapping = {
                "patient_id": "patient.reference",
        }
        instance_dict = {
                'origin': self.origin,
        }
        for dest, source in mapping.items():
            instance_dict[dest] = get_value_at_json_path(source)
        return instance_dict


    def normalize(self):
        for record in self.data["contained"]:
            if "gender" in record:
                record["gender"] = GenderNormalizer.normalize(record["gender"])
