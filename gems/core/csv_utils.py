from .models import Survey, SurveyResult, Contact
from dateutil import parser
from datetime import datetime


def process_file(filename):
    errors = []
    i = 0

    try:

        fin = open(filename, 'r')
        headers = None
        header_map = {}
        survey_index = 0
        survey_key_index = 0
        contact_index = 0
        contact_key_index = 0
        date_index = 0

        for line in fin:
            parts = split_line(line)

            if i == 0:
                header_map, survey_index, survey_key_index, contact_index, contact_key_index, date_index = \
                    process_header(parts)
                headers = parts
            else:
                result, error = process_line(survey_index, survey_key_index, contact_index, contact_key_index,
                                             date_index, header_map, headers, parts)

                if result == 0:
                    errors.append({"row": i + 1, "error": error})

            i = i + 1

        fin.close()
    except Exception as ex:
        errors.append({"row": i + 1, "error": "%s" % ex})

    return errors, i

def split_line(line):
    if line:
        parts = line.split(",")

        for i in range(0, len(parts)):
            parts[i] = parts[i].strip()

        return parts
    else:
        return None


def process_header(parts):
    header_map = {}
    survey_index = 0
    survey_key_index = 0
    contact_index = 0
    contact_key_index = 0
    date_index = 0
    i = 0

    for part in parts:
        header_map[part] = i
        name = part.lower()

        if name == "survey":
            survey_index = i
        elif name == "survey_key":
            survey_key_index = i
        elif name == "msisdn":
            contact_index = i
        elif name == "key":
            contact_key_index = i
        elif name == "timestamp":
            date_index = i

        i = i + 1

    return header_map, survey_index, survey_key_index, contact_index, contact_key_index, date_index


def survey_lookup(name, key):
    if key:
        survey = Survey.objects.filter(survey_id__exact=key).first()
    else:
        survey = Survey.objects.filter(name__exact=name).first()

    if survey is None:
        survey = Survey.objects.create(survey_id=key, name=name)

    return survey


def contact_lookup(msisdn, key):
    contact = Contact.objects.filter(msisdn__exact=msisdn).first()

    if contact is None:
        contact = Contact.objects.create(msisdn=msisdn, vkey=key)

    return contact


def process_line(survey_index, survey_key_index, contact_index,
                 contact_key_index, date_index, header_map, headers, results):
    try:
        i = 0
        answers = {}
        survey = None
        contact = None
        date = datetime.now()

        for result in results:
            if survey_index == i:
                key = None

                if "survey_key" in header_map.keys():
                    key = results[header_map["survey_key"]]

                survey = survey_lookup(result, key)
            elif survey_key_index == i:
                pass
            elif contact_index == i:
                key = None

                if "key" in header_map.keys():
                    key = results[header_map["key"]]

                contact = contact_lookup(result, key)
            elif contact_key_index == i:
                pass
            elif date_index == i:
                date = parser.parse(result)
            else:
                answers[headers[i]] = result

            i = i + 1

        if survey and contact and len(answers.keys()) > 0:
            sr = SurveyResult(
                survey=survey,
                contact=contact,
                created_at=date,
                answer=answers
            )

            for field in sr._meta.local_fields:
                if field.name == "created_at":
                    field.auto_now_add = False
                    break;

            sr.save()

            for field in sr._meta.local_fields:
                if field.name == "created_at":
                    field.auto_now_add = True
                    break;
        else:
            return 0, "Survey, Contact and at least 1 answer is required"

        return 1, None
    except Exception as ex:
        return 0, "%s" %    ex