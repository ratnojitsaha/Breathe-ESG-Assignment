# API

Base URL: `/api/`

All list endpoints are paginated with DRF page-number pagination.

## Companies

`GET /companies/`

Returns tenant companies.

## Data Sources

`GET /data-sources/?company=1`

Filters: `company`, `source_type`, `active`.

## Uploads

`POST /uploads/upload/`

Multipart fields:

- `company`: company id
- `data_source`: data source id
- `file`: CSV or JSON upload

Accepted formats are enforced by source:

- SAP fuel/procurement: `.csv`
- Utility electricity: `.csv`
- Corporate travel: `.json`

Successful uploads are normalized immediately. Rows with validation findings are routed to analyst review before audit locking.

`GET /uploads/?company=1`

Filters: `company`, `source_type`, `status`.

## Raw Records

`GET /raw-records/?company=1`

Filters: `company`, `raw_upload`, `parsing_status`.

## Normalized Records

`GET /normalized-records/?company=1&review_status=NEEDS_REVIEW`

Filters: `company`, `source_type`, `review_status`, `locked_for_audit`, `scope_category`.

`POST /normalized-records/{id}/review/`

Body:

```json
{
  "status": "APPROVED",
  "comment": "Analyst accepted row."
}
```

Approval locks the row for audit. Rejection leaves it unlocked but records review history.

## Validation Issues

`GET /validation-issues/?company=1`

Filters: `company`, `severity`, `code`, `normalized_record`, `raw_record`.

## Audit Logs

`GET /audit-logs/?company=1`

Filters: `company`, `action`, `entity_type`, `entity_id`.
