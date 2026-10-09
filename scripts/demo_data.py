"""Sample properties + document text used by seed_demo.py and the engine tests."""

SCENARIOS = [
    {
        "title": "Green Valley Villa",
        "property_type": "Residential", "survey_number": "118/2", "area_sq_ft": 1200,
        "address": "14, Green Valley Road", "locality": "Dharampeth", "city": "Nagpur",
        "state": "Maharashtra", "pincode": "440010", "lat": 21.1380, "lng": 79.0650,
        "docs": [
            ("Title Deed", "TITLE DEED\nOwner: Rajesh Kumar Sharma\nSurvey No: 118/2\nArea: 1200 sq ft\nDate: 12/03/2019\nDharampeth, Nagpur PIN 440010"),
            ("Tax Receipt", "PROPERTY TAX RECEIPT\nOwner Name: Rajesh Kumar Sharma\nSurvey No. 118/2\nBuilt-up area 1,200 sq ft\nPaid on 05/04/2024\nAmount Rs. 8,450\nNagpur 440010"),
            ("Sale Agreement", "AGREEMENT FOR SALE\nSeller: Rajesh Kumar Sharma\nBuyer: Amit Verma\nSurvey No: 118/2\nArea: 1200 sq ft\nDate: 20 August 2024\nConsideration Rs. 5,500,000"),
        ],
        "expect": "Low",
    },
    {
        "title": "Sunrise Apartment 4B",
        "property_type": "Residential", "survey_number": "77", "area_sq_ft": 950,
        "address": "Sunrise Heights, Flat 4B", "locality": "Manish Nagar", "city": "Nagpur",
        "state": "Maharashtra", "pincode": "440015", "lat": 21.1002, "lng": 79.0490,
        "docs": [
            ("Title Deed", "TITLE DEED\nOwner: Priya Deshmukh\nSurvey No: 77\nArea: 950 sq ft\nDate: 02/11/2018"),
            ("Tax Receipt", "PROPERTY TAX RECEIPT\nOwner Name: Priya Deshpande\nSurvey No: 77\nArea: 1200 sq ft\nDate: 10/04/2024\nPIN 440015"),
        ],
        "expect": "Medium",
    },
    {
        "title": "Farmland Plot 52",
        "property_type": "Agricultural", "survey_number": "52", "area_sq_ft": 43560,
        "address": "Gat No 52, Near Bansi Nagar", "locality": "Hingna", "city": "Nagpur",
        "state": "Maharashtra", "pincode": "441110", "lat": 21.0900, "lng": 78.9800,
        "docs": [
            ("Title Deed", "TITLE DEED\nOwner: Sanjay Patil\nSurvey No: 52\nArea: 43560 sq ft\nDate: 15/06/2015"),
            ("Sale Agreement", "AGREEMENT FOR SALE\nSeller: Mahesh Rane\nBuyer: Kiran Joshi\nSurvey No: 58\nArea: 52000 sq ft\nDate: 03/01/2012"),
            ("Tax Receipt", "PROPERTY TAX RECEIPT\nOwner Name: Sanjay Patil\nSurvey No: 52\nArea: 43560 sq ft\nDate: 09/09/2031"),
        ],
        "expect": "High",
    },
    {
        "title": "Riverside Commercial Complex",
        "property_type": "Commercial", "survey_number": "204/A", "area_sq_ft": 3200,
        "address": "Riverside Complex, Shop Block C", "locality": "Andheri East", "city": "Mumbai",
        "state": "Maharashtra", "pincode": "400069", "lat": 19.1136, "lng": 72.8697,
        "docs": [
            ("Title Deed", "TITLE DEED\nOwner: Anil Kapadia\nProprietor of: Meera Enterprises Pvt Ltd\nSurvey No: 204/A\nArea: 3200 sq ft\nDate: 18/01/2016\nAndheri East, Mumbai PIN 400069"),
            ("Tax Receipt", "PROPERTY TAX RECEIPT\nOwner Name: Anil Kapadia\nSurvey No. 204/A\nBuilt-up area 3,200 sq ft\nPaid on 12/04/2024\nAmount Rs. 62,000\nMumbai 400069"),
            ("Sale Agreement", "AGREEMENT FOR SALE\nSeller: Anil Kapadia\nBuyer: Meera Enterprises Pvt Ltd\nSurvey No: 204/A\nArea: 3200 sq ft\nDate: 5 February 2016\nConsideration Rs. 18,500,000"),
        ],
        "expect": "Low",
    },
    {
        "title": "Whispering Pines Farmhouse",
        "property_type": "Agricultural", "survey_number": "31/1", "area_sq_ft": 21780,
        "address": "Gat No 31/1, Near Pine Ridge", "locality": "Igatpuri", "city": "Nashik",
        "state": "Maharashtra", "pincode": "422403", "lat": 19.6996, "lng": 73.5626,
        "docs": [
            ("Title Deed", "TITLE DEED\nOwner: Vithal Rao Jadhav\nSurvey No: 31/1\nArea: 21780 sq ft\nDate: 22/07/2014"),
            ("Tax Receipt", "PROPERTY TAX RECEIPT\nOwner Name: Vithal Rao Jadhav\nSurvey No. 31/1\nArea 18000 sq ft\nPaid on 14/04/2024\nAmount Rs. 4,200\nNashik 422404"),
        ],
        "expect": "Medium",
    },
    {
        "title": "Tech Park Office Unit 12B",
        "property_type": "Commercial", "survey_number": "88", "area_sq_ft": 1450,
        "address": "Cyber Tech Park, Tower 2, Unit 12B", "locality": "Hinjewadi", "city": "Pune",
        "state": "Maharashtra", "pincode": "411057", "lat": 18.5912, "lng": 73.7389,
        "docs": [
            ("Title Deed", "TITLE DEED\nOwner: Nikhil Rane\nSurvey No: 88\nArea: 1450 sq ft\nDate: 09/09/2020\nHinjewadi, Pune PIN 411057"),
            ("Tax Receipt", "PROPERTY TAX RECEIPT\nOwner Name: Nikhil Rane\nSurvey No. 88\nBuilt-up area 1,450 sq ft\nPaid on 01/04/2024\nAmount Rs. 21,300\nPune 411057"),
            ("NOC", "NO OBJECTION CERTIFICATE\nIssued to: Nikhil Rane\nSurvey No: 88\nSociety: Cyber Tech Park Owners Association\nDate: 15 March 2024"),
        ],
        "expect": "Low",
    },
    {
        "title": "Heritage Bungalow",
        "property_type": "Residential", "survey_number": "45", "area_sq_ft": 2600,
        "address": "12, Heritage Lane", "locality": "Civil Lines", "city": "Delhi",
        "state": "Delhi", "pincode": "110054", "lat": 28.6785, "lng": 77.2216,
        "docs": [
            ("Title Deed", "TITLE DEED\nOwner: Harbans Singh Chadha\nSurvey No: 45\nArea: 2600 sq ft\nDate: 11/05/2009"),
            ("Sale Agreement", "AGREEMENT FOR SALE\nSeller: Rakesh Malhotra\nBuyer: Sunita Malhotra\nSurvey No: 45\nArea: 2600 sq ft\nDate: 30 November 2033\nConsideration Rs. 42,000,000"),
            ("Tax Receipt", "PROPERTY TAX RECEIPT\nOwner Name: Harbans Singh Chadha\nSurvey No. 54\nArea 2600 sq ft\nPaid on 06/04/2024\nDelhi 110054"),
        ],
        "expect": "High",
    },
    {
        "title": "Sunset Orchard",
        "property_type": "Agricultural", "survey_number": "63/2", "area_sq_ft": 32670,
        "address": "Gat No 63/2, Chandur Road", "locality": "Chandur Bazar", "city": "Amravati",
        "state": "Maharashtra", "pincode": "444905", "lat": 20.9374, "lng": 77.7796,
        "docs": [
            ("Title Deed", "TITLE DEED\nOwner: Dattatray Wankhede\nSurvey No: 63/2\nArea: 32670 sq ft\nDate: 04/03/2013"),
            ("Tax Receipt", "PROPERTY TAX RECEIPT\nOwner Name: Dattatray Wankhede\nSurvey No. 63/2\nArea 32670 sq ft\nPaid on 20/04/2024\nAmount Rs. 3,100\nAmravati 444905"),
            ("Sale Agreement", "AGREEMENT FOR SALE\nSeller: Dattatray Wankhede\nBuyer: Prakash Ingle\nSurvey No: 63/2\nArea: 32670 sq ft\nDate: 2 June 2023\nConsideration Rs. 2,900,000"),
        ],
        "expect": "Low",
    },
    {
        "title": "Silver Oak Apartments 302",
        "property_type": "Residential", "survey_number": "17", "area_sq_ft": 1050,
        "address": "Silver Oak Apartments, Flat 302", "locality": "Whitefield", "city": "Bangalore",
        "state": "Karnataka", "pincode": "560066", "lat": 12.9698, "lng": 77.7500,
        "docs": [
            ("Title Deed", "TITLE DEED\nOwner: Lakshmi Narayanan\nSurvey No: 17\nArea: 1050 sq ft\nDate: 19/08/2019"),
            ("Tax Receipt", "PROPERTY TAX RECEIPT\nOwner Name: Lakshmi Narayanan\nSurvey No. 71\nArea 1120 sq ft\nPaid on 09/04/2024\nBangalore 560066"),
        ],
        "expect": "Medium",
    },
    {
        "title": "Industrial Shed Plot 9",
        "property_type": "Other", "survey_number": "9", "area_sq_ft": 8000,
        "address": "Plot 9, Phase II Industrial Estate", "locality": "Jeedimetla", "city": "Hyderabad",
        "state": "Telangana", "pincode": "500055", "lat": 17.5125, "lng": 78.4569,
        "docs": [
            ("Title Deed", "TITLE DEED\nOwner: Srinivas Reddy Industries\nSurvey No: 9\nArea: 8000 sq ft\nDate: 27/02/2017\nJeedimetla, Hyderabad PIN 500055"),
            ("Tax Receipt", "PROPERTY TAX RECEIPT\nOwner Name: Srinivas Reddy Industries\nSurvey No. 9\nArea 8000 sq ft\nPaid on 03/04/2024\nAmount Rs. 55,000\nHyderabad 500055"),
            ("NOC", "NO OBJECTION CERTIFICATE\nIssued to: Srinivas Reddy Industries\nSurvey No: 9\nAuthority: Industrial Area Local Authority\nDate: 21 January 2024"),
        ],
        "expect": "Low",
    },
    {
        "title": "Lakeview Weekend Villa",
        "property_type": "Residential", "survey_number": "5/3A", "area_sq_ft": 2500,
        "address": "Lakeview Colony, Plot 5/3", "locality": "Sevagram Road", "city": "Wardha",
        "state": "Maharashtra", "pincode": "442001", "lat": 20.7453, "lng": 78.6022,
        "docs": [
            ("Sale Agreement", "AGREEMENT FOR SALE\nSeller: Bhaskar Tiwari\nBuyer: Neha Tiwari\nSurvey No: 5/3\nArea: 1800 sq ft\nDate: 8 May 2022\nConsideration Rs. 3,200,000"),
            ("Title Deed", "AGREEMENT FOR SALE\nSeller: Bhaskar Tiwari\nBuyer: Neha Tiwari\nSurvey No: 5/3\nArea: 1800 sq ft\nDate: 8 May 2022\nConsideration Rs. 3,200,000"),
        ],
        "expect": "High",
    },
    {
        "title": "Central Market Shop No. 5",
        "property_type": "Commercial", "survey_number": "112", "area_sq_ft": 600,
        "address": "Central Market Complex, Shop No. 5", "locality": "T Nagar", "city": "Chennai",
        "state": "Tamil Nadu", "pincode": "600017", "lat": 13.0418, "lng": 80.2341,
        "docs": [
            ("Title Deed", "TITLE DEED\nOwner: Ramanathan Subramaniam\nSurvey No: 112\nArea: 600 sq ft\nDate: 14/12/2011\nT Nagar, Chennai PIN 600017"),
            ("Tax Receipt", "PROPERTY TAX RECEIPT\nOwner Name: Ramanathan Subramaniam\nSurvey No. 112\nArea 600 sq ft\nPaid on 11/04/2024\nAmount Rs. 9,800\nChennai 600017"),
        ],
        "expect": "Low",
    },
    {
        "title": "Green Acres Plot 21",
        "property_type": "Other", "survey_number": "21", "area_sq_ft": 5400,
        "address": "Green Acres Layout, Plot 21", "locality": "Wathoda", "city": "Nagpur",
        "state": "Maharashtra", "pincode": "440008", "lat": 21.1580, "lng": 79.1290,
        "docs": [
            ("Title Deed", "TITLE DEED\nOwner: Ashwini Tiwari\nSurvey No: 21\nArea: 4500 sq ft\nDate: 03/10/2021\nWathoda, Nagpur PIN 440027"),
            ("Tax Receipt", "PROPERTY TAX RECEIPT\nOwner Name: Ashwini Tiwari\nSurvey No. 21\nArea 4500 sq ft\nPaid on 17/04/2024\nAmount Rs. 7,650"),
        ],
        "expect": "Medium",
    },
]
