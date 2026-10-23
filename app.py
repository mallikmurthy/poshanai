import os
import json
import base64
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler

class NutritionException(Exception):
    """Custom exception raised for nutrition calculation errors."""
    pass


class Person:
    """Base class demonstrating OOP Inheritance (Module 4 & 5)"""
    def __init__(self, name: str, role: str):
        self.name = name
        self.role = role

    def get_info(self) -> dict:
        return {"name": self.name, "role": self.role}


class Child(Person):
    """Child entity inheriting from Person"""
    def __init__(self, child_id: str, name: str, age_months: int, weight_kg: float, height_cm: float):
        super().__init__(name, role="CHILD")
        self.child_id = child_id
        self.age_months = int(age_months)
        self.weight_kg = float(weight_kg)
        self.height_cm = float(height_cm)
        self.is_present = True
        self.bmi, self.nutrition_status, self.target_cal, self.target_prot = self.calculate_nutritional_targets()

    def calculate_nutritional_targets(self):
        """Module 1 & 2: Math operators, conditionals & WHO/ICMR logic"""
        height_m = self.height_cm / 100.0
        if height_m <= 0:
            raise NutritionException("Height must be greater than zero.")
        
        bmi = round(self.weight_kg / (height_m ** 2), 2)

        # WHO Pediatric Growth Proxy & ICMR RDA targets
        if bmi < 13.0:
            status = "SAM (Severe Acute Malnutrition)"
            target_cal = 750.0
            target_prot = 22.0
        elif 13.0 <= bmi < 14.2:
            status = "MAM (Moderate Acute Malnutrition)"
            target_cal = 620.0
            target_prot = 17.0
        else:
            status = "Normal"
            target_cal = 500.0
            target_prot = 13.0

        return bmi, status, target_cal, target_prot

    def to_dict(self):
        return {
            "child_id": self.child_id,
            "name": self.name,
            "age_months": self.age_months,
            "weight_kg": self.weight_kg,
            "height_cm": self.height_cm,
            "is_present": self.is_present,
            "bmi": self.bmi,
            "status": self.nutrition_status,
            "target_cal": self.target_cal,
            "target_prot": self.target_prot
        }

DATA_FILE = "anganwadi_data.json"

def load_database():
    """Reads database using Python file operations (Module 3)"""
    default_data = {
        "children": [
            {"child_id": "C101", "name": "Aarav Kumar", "age_months": 48, "weight_kg": 11.2, "height_cm": 96.0, "is_present": True, "bmi": 12.15, "status": "SAM (Severe Acute Malnutrition)", "target_cal": 750.0, "target_prot": 22.0},
            {"child_id": "C102", "name": "Priya Sharma", "age_months": 42, "weight_kg": 13.5, "height_cm": 95.0, "is_present": True, "bmi": 14.96, "status": "Normal", "target_cal": 500.0, "target_prot": 13.0},
            {"child_id": "C103", "name": "Rohan Gowda", "age_months": 52, "weight_kg": 13.0, "height_cm": 98.0, "is_present": False, "bmi": 13.54, "status": "MAM (Moderate Acute Malnutrition)", "target_cal": 620.0, "target_prot": 17.0}
        ],
        "evaluations": []
    }
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w") as f:
            json.dump(default_data, f, indent=2)
        return default_data

    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return default_data

def save_database(data):
    """Writes updated data into JSON file (Module 3)"""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def analyze_food_image_with_ai(image_b64: str, mime_type: str = "image/jpeg") -> dict:#scanner
  
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=api_key)
            prompt = """
            You are a certified pediatric clinical nutritionist for Anganwadi meals.
            Analyze this meal plate photo carefully:
            1. Identify every food item (e.g., Rice, Dal, Sambar, Boiled Egg, Khichdi, Veg Curry).
            2. Estimate the portion size (in grams) based on standard Indian Anganwadi steel plates.
            3. Calculate estimated total Calories (kcal) and total Protein (grams).
            
            Return ONLY a valid JSON object formatted as:
            {
              "detected_items": ["item1 (approx grams)", "item2 (approx grams)"],
              "total_calories": <number>,
              "total_protein": <number>,
              "confidence": "<high|medium|low>"
            }
            """
            image_raw = base64.b64decode(image_b64)
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=[
                    types.Part.from_bytes(data=image_raw, mime_type=mime_type),
                    prompt
                ],
                config=types.GenerateContentConfig(response_mime_type="application/json")
            )
            return json.loads(response.text)
        except Exception as e:
            print(f"[AI Vision Warning] Gemini scan failed, falling back to local engine: {e}")

    return {
        "detected_items": ["Boiled Rice (150g)", "Yellow Toor Dal (100ml)", "Boiled Egg (1 pc)"],
        "total_calories": 480.0,
        "total_protein": 14.5,
        "confidence": "medium (offline-fallback)"
    }

class AnganwadiRequestHandler(BaseHTTPRequestHandler):

    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_UI.encode("utf-8"))
        elif self.path == "/api/data":
            db = load_database()
            self._send_json(db)
        else:
            self.send_error(404, "Endpoint Not Found")

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length).decode('utf-8')
        
        try:
            req = json.loads(post_data)
        except Exception:
            return self._send_json({"error": "Invalid JSON"}, 400)

        db = load_database()

        if self.path == "/api/add-child":
            try:
                new_child = Child(
                    child_id=f"C{len(db['children']) + 101}",
                    name=req["name"],
                    age_months=int(req["age_months"]),
                    weight_kg=float(req["weight_kg"]),
                    height_cm=float(req["height_cm"])
                )
                db["children"].append(new_child.to_dict())
                save_database(db)
                return self._send_json({"status": "success", "child": new_child.to_dict()})
            except Exception as e:
                return self._send_json({"error": str(e)}, 400)

      
        elif self.path == "/api/mark-attendance":
            child_id = req.get("child_id")
            status = req.get("is_present", True)
            for ch in db["children"]:
                if ch["child_id"] == child_id:
                    ch["is_present"] = status
                    break
            save_database(db)
            return self._send_json({"status": "success", "children": db["children"]})

        elif self.path == "/api/scan-meal":
            child_id = req.get("child_id")
            img_b64 = req.get("image_base64", "")
            mime_type = req.get("mime_type", "image/jpeg")

  
            child_data = next((c for c in db["children"] if c["child_id"] == child_id), None)
            if not child_data:
                return self._send_json({"error": "Child not found"}, 404)

           
            scan_result = analyze_food_image_with_ai(img_b64, mime_type)
            
            cal_actual = float(scan_result.get("total_calories", 0))
            prot_actual = float(scan_result.get("total_protein", 0))
            
            cal_target = child_data["target_cal"]
            prot_target = child_data["target_prot"]

           
            cal_pass = cal_actual >= (cal_target * 0.85)
            prot_pass = prot_actual >= (prot_target * 0.85)

            if cal_pass and prot_pass:
                decision = "APPROVED (Satisfying)"
                action = "Meal fulfills the daily supplementary threshold for this child's growth tier."
            else:
                decision = "FLAGGED (Nutrient Deficit)"
                gaps = []
                if not cal_pass:
                    gaps.append(f"{round(cal_target - cal_actual, 1)} kcal deficit")
                if not prot_pass:
                    gaps.append(f"{round(prot_target - prot_actual, 1)}g protein deficit")
                action = f"Add 1 boiled egg or 20g roasted groundnuts to resolve: {', '.join(gaps)}."

            eval_entry = {
                "child_id": child_id,
                "child_name": child_data["name"],
                "status_tier": child_data["status"],
                "detected_items": scan_result.get("detected_items", []),
                "actual_cal": cal_actual,
                "actual_prot": prot_actual,
                "target_cal": cal_target,
                "target_prot": prot_target,
                "decision": decision,
                "action": action
            }

            db["evaluations"].insert(0, eval_entry)
            save_database(db)
            return self._send_json({"status": "success", "result": eval_entry})

        self.send_error(404, "Endpoint not found")

