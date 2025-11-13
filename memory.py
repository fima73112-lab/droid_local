import json, os, datetime

class Memory:
    def __init__(self, file="memory.json"):
        self.file = file
        if not os.path.exists(file):
            with open(file, "w") as f:
                json.dump({"history": [], "patterns": {}}, f)
        with open(file, "r") as f:
            self.data = json.load(f)

    def add(self, event_type, description, file_name=None, error=None, fix=None):
        entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "type": event_type,
            "description": description,
            "file": file_name,
            "error": error,
            "fix": fix,
        }
        self.data["history"].append(entry)
        self._save()

    def _save(self):
        with open(self.file, "w") as f:
            json.dump(self.data, f, indent=2)

    def get_context(self, limit=10):
        """Последние события"""
        return "\n".join(
            f"[{x['type']}] {x['description']}" for x in self.data["history"][-limit:]
        )

    def get_recent_errors(self, limit=5):
        return [x for x in self.data["history"] if x["type"] == "error"][-limit:]

    def learn_pattern(self, pattern, fix):
        self.data["patterns"][pattern] = fix
        self._save()

    def find_pattern(self, error_text):
        for pattern, fix in self.data["patterns"].items():
            if pattern.lower() in error_text.lower():
                return fix
        return None
