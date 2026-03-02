# BAP Endpoint Structures

This document outlines the request and response structures used by the various agent tools interacting with the Vistaar Beckn APIs (`BAP_ENDPOINT`). All requests share a common `context` object, with modifications in `action`, `message`, and `domain` specific properties.

## 1. Weather Forecast (`weather.py`)
- **Endpoint:** `/search`
- **Action:** `search`

### Request Payload (`WeatherRequest`)
Sends the geographic coordinates for location-based weather data.
```json
{
  "context": {
    "domain": "schemes:vistaar",
    "action": "search",
    "version": "1.1.0",
    "bap_id": "...", "bap_uri": "...",
    "bpp_id": "...", "bpp_uri": "...",
    "transaction_id": "<uuid>",
    "message_id": "<uuid>",
    "timestamp": "<timestamp>",
    "ttl": "PT10M",
    "location": { "country": { "code": "IND" }, "city": { "code": "*" } }
  },
  "message": {
    "intent": {
      "category": {
        "descriptor": { "name": "Weather-Forecast", "code": "WFC" }
      },
      "fulfillment": {
        "stops": [
          {
            "location": { "lat": "<latitude>", "lon": "<longitude>" }
          }
        ]
      }
    }
  }
}
```

### Response Model (`WeatherResponse`)
Returns catalog consisting of multiple providers and items containing the weather data fields.
- `context`: Echoes back the context context data.
- `responses[].message.catalog.providers[]`: Contains weather providers.
- `providers[].items[]`: Contains `descriptor` (short/long description) and `tags` (groupings of tag items related to the weather attributes like temp, humidity, etc.).

---

## 2. Scheme Information (`scheme_info.py`)
- **Endpoint:** `/search`
- **Action:** `search`

### Request Payload (`SchemeRequest`)
Seeks basic informational data about an agricultural scheme.
```json
{
  "context": { "domain": "schemes:vistaar", "action": "search", ... },
  "message": {
    "intent": {
      "category": {
        "descriptor": { "code": "schemes-agri" }
      },
      "item": {
        "descriptor": { "name": "<scheme_name_e_g_kcc_pmkisan>" }
      }
    }
  }
}
```

### Response Model (`SchemeResponse`)
- `responses[].message.catalog.providers[].items[]`: The scheme items containing a `descriptor` and multiple `tags` lists.
- Each `tag` group enumerates details like eligibility criteria, benefits, application processes, etc. for the specific scheme.

---

## 3. Mandi Price Discovery (`mandi.py`)
- **Endpoint:** `/search`
- **Action:** `search`

### Request Payload (`MandiRequest`)
Queries commodity price ranges over a specific timeframe and near a particular geolocation.
```json
{
  "context": { "domain": "schemes:vistaar", "action": "search", ... },
  "message": {
    "intent": {
      "category": { "descriptor": { "code": "price-discovery" } },
      "item": { "descriptor": { "code": "mandi" } },
      "fulfillment": {
        "stops": [
          {
            "location": { "lat": "<latitude>", "lon": "<longitude>" },
            "time": { "range": { "start": "<start_date_iso>", "end": "<end_date_iso>" } },
            "commoditycode": "<agmkt_commodity_code>"
          }
        ]
      }
    }
  }
}
```

### Response Model (`MandiResponse`)
- providers contain `items` (of type `MandiItem`).
- Each `MandiItem` extracts standard values from tags: `Commodity`, `Market`, `District`, `State`, `Modal Price`, `Min Price`, `Max Price`, `Price Unit`, `Arrival Date`, etc.

---

## 4. PM Kisan Scheme Status (`pmkisan_scheme_status.py`)
This tool involves a two-step API process: **Init** for OTP generation, and **Status** for validation and status fetching.

### 4.1. Init Request
- **Endpoint:** `/init`
- **Action:** `init`

```json
{
  "context": { "domain": "schemes:vistaar", "action": "init", ... },
  "message": {
    "order": {
      "provider": { "id": "" },
      "items": [ { "id": "" } ],
      "fulfillments": [
        {
          "customer": {
            "person": {
              "name": "Customer Name",
              "tags": [
                {
                  "display": true,
                  "descriptor": { "name": "Registration Details", "code": "reg-details" },
                  "list": [
                    {
                      "descriptor": { "name": "Registration Number", "code": "reg-number" },
                      "value": "<registration_number>",
                      "display": true
                    }
                  ]
                }
              ]
            },
            "contact": { "phone": "<phone_number>" }
          }
        }
      ]
    }
  }
}
```

### 4.2. Status Request (With OTP)
- **Endpoint:** `/status`
- **Action:** `status`

```json
{
  "context": { "domain": "schemes:vistaar", "action": "status", ... },
  "message": {
    "order_id": "<otp_from_user>"
  }
}
```

### Response Model (`SchemeStatusResponse`)
The status payload returns user-specific context.
- `responses[].message.order`: Represents the user's status payload.
- Contains `state`, `provider`, `items`, `fulfillments` (with customer details and status state flags), and various descriptive `tags`.

---

## 5. PMFBY Scheme Status (`pmfby_scheme_status.py`)
Similarly handles a two-step Init (OTP generation) followed by Status retrieval. Differs slightly in tags and format.

### 5.1. Init Request (Get OTP)
- **Endpoint:** `/init`
- **Action:** `init`

```json
{
  "context": { "domain": "schemes:vistaar", "action": "init", ... },
  "message": {
    "order": {
      "provider": { "id": "pmfby-agri" },
      "items": [ { "id": "pmfby" } ],
      "fulfillments": [
        {
          "customer": {
            "person": {
              "tags": [
                { "descriptor": { "code": "request_type" }, "value": "get_otp" },
                { "descriptor": { "code": "phone_number" }, "value": "<phone_number_without_country_code>" }
              ]
            },
            "contact": { "phone": "<phone_number_without_country_code>" }
          }
        }
      ]
    }
  }
}
```

### 5.2. Status Request (Validate OTP & Query)
- **Endpoint:** `/status`
- **Action:** `status`

```json
{
  "context": { "domain": "schemes:vistaar", "action": "status", ... },
  "message": {
    "order_id": "<otp_6_digits>",
    "order": {
      "id": "order-1",
      "provider": { "id": "pmfby-agri" },
      "items": [ { "id": "pmfby" } ],
      "fulfillments": [
        {
          "customer": {
            "person": {
              "tags": [
                { "descriptor": { "code": "inquiry_type" }, "value": "<policy_status|claim_status>" },
                { "descriptor": { "code": "year" }, "value": "<year>" },
                { "descriptor": { "code": "season" }, "value": "<Kharif|Rabi|Summer>" }
              ]
            },
            "contact": { "phone": "<phone_number_without_country_code>" }
          }
        }
      ]
    }
  }
}
```

---

## 6. Soil Health Card (SHC) Status (`shc_scheme_status.py`)
Fetches soil health card information and downloads generated PDF/HTML reports.

### Request Payload (`SHCStatusRequest`)
- **Endpoint:** `/init`
- **Action:** `init`

```json
{
  "context": { "domain": "schemes:vistaar", "action": "init", ... },
  "message": {
    "order": {
      "provider": { "id": "shc-discovery" },
      "items": [ { "id": "soil-health-card" } ],
      "fulfillments": [
        {
          "customer": {
            "person": {
              "tags": [
                { "descriptor": { "code": "cycle" }, "value": "<cycle_year_e_g_2023_24>" }
              ]
            },
            "contact": { "phone": "<phone_number_formatted>" }
          }
        }
      ]
    }
  }
}
```

### Response Model (`SHCStatusResponse`)
- Returns HTML/Base64 payloads attached to media properties representing soil test insights.
- The `items` array nodes contain `media` resources.
- Responses undergo post-processing (HTML decoding, injection, and PDF generation cache logic) to present structured markdown to the LLM agent.
