import asyncio
import threading
import queue
import time
import hashlib
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie, PydanticObjectId
from src.models.user import User
from src.models.detection import Detection

class DatabaseManager:
    def __init__(self, connection_string, client_id="User_Generico"):
        self.connection_string = connection_string
        self.client_id = client_id
        self.log_queue = queue.Queue()
        self.is_running = True
        self.is_initialized = False
        self.init_error = None
        
        # Gestione loop asincrono per Beanie in un thread dedicato
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self._start_async_loop, daemon=True)
        self.thread.start()
        
        # Avvia il worker per svuotare la coda dei log
        self.worker_thread = threading.Thread(target=self._log_worker, daemon=True)
        self.worker_thread.start()

    def _start_async_loop(self):
        asyncio.set_event_loop(self.loop)
        try:
            self.loop.run_until_complete(self._initialize_beanie())
            self.loop.run_forever()
        except Exception as e:
            self.init_error = str(e)
            print(f"❌ Crash loop asincrono: {e}")

    async def _initialize_beanie(self):
        """Inizializza la connessione asincrona e i modelli Beanie."""
        try:
            if not self.connection_string or "mongodb+srv" not in self.connection_string:
                self.init_error = "Stringa di connessione non valida nel file .env"
                return

            client = AsyncIOMotorClient(self.connection_string, serverSelectionTimeoutMS=5000)
            # Verifica fisica della connessione prima di procedere
            await client.admin.command('ping')
            
            if not hasattr(client.__class__, 'append_metadata'):
                def append_metadata(self, metadata): pass
                client.__class__.append_metadata = append_metadata

            # Recupera il database (accesso corretto per Motor)
            self.db = client.get_database("DeepWatchDB")
            
            await init_beanie(database=self.db, document_models=[User, Detection])
            
            # Assicura admin di default
            await self._ensure_default_user()
            self.is_initialized = True
            print("✅ Beanie ODM inizializzato con successo.")
        except Exception as e:
            self.init_error = f"Errore Cloud: {str(e)}"
            print(f"⚠️ Errore inizializzazione Beanie: {e}")

    async def _ensure_default_user(self):
        count = await User.count()
        if count == 0:
            admin = User(
                username="admin",
                password_hash=self._hash_password("admin123"),
                company="DeepWatch Pro"
            )
            await admin.insert()
            print("ℹ️ Creato utente admin predefinito via Beanie")

    def _hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def authenticate(self, username, password):
        """Metodo sincrono per la UI (usa il loop asincrono internamente)."""
        if not self.is_initialized:
            return False, "Database non ancora pronto"
            
        async def _auth_task():
            user = await User.find_one(User.username == username)
            if user and user.password_hash == self._hash_password(password):
                return True, user.dict()
            return False, "Username o Password errati"

        future = asyncio.run_coroutine_threadsafe(_auth_task(), self.loop)
        return future.result()

    def register_user(self, username, password, company="DeepWatch Security"):
        """Crea un nuovo utente nel database."""
        if not self.is_initialized:
            print("❌ Registrazione fallita: Database non inizializzato")
            return False, "Database non ancora pronto"

        async def _register_task():
            try:
                print(f"🔍 Controllo esistenza utente: {username}")
                existing = await User.find_one(User.username == username)
                if existing:
                    print(f"⚠️ Utente {username} già esistente")
                    return False, "Username già in uso"
                
                print(f"📝 Creazione nuovo utente: {username} per {company}")
                new_user = User(
                    username=username,
                    password_hash=self._hash_password(password),
                    company=company
                )
                await new_user.insert()
                print(f"✅ Utente {username} salvato con successo!")
                return True, "Registrazione completata!"
            except Exception as e:
                print(f"❌ Errore durante insert utente: {e}")
                return False, str(e)

        future = asyncio.run_coroutine_threadsafe(_register_task(), self.loop)
        try:
            return future.result(timeout=10)
        except Exception as e:
            print(f"❌ Timeout o errore future registrazione: {e}")
            return False, f"Timeout connessione: {e}"

    def log_detection(self, camera_name, detections, frame=None):
        if not detections:
            return
            
        import cv2
        import base64

        img_base64 = ""
        if frame is not None:
            try:
                # Comprimi per non saturare il database
                _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 50])
                img_base64 = base64.b64encode(buffer).decode('utf-8')
            except Exception as e:
                print(f"⚠️ Errore codifica immagine: {e}")

        log_entry = {
            "client_id": self.client_id,
            "camera": camera_name,
            "objects": detections,
            "object_count": len(detections),
            "image": img_base64,
            "timestamp": datetime.now()
        }
        self.log_queue.put(log_entry)

    def _log_worker(self):
        """Svuota la coda sincrona e invia al database in modo asincrono."""
        while self.is_running:
            try:
                if not self.is_initialized:
                    time.sleep(2)
                    continue

                try:
                    data = self.log_queue.get(timeout=1)
                except queue.Empty:
                    continue

                async def _save_task():
                    doc = Detection(**data)
                    await doc.insert()
                
                asyncio.run_coroutine_threadsafe(_save_task(), self.loop)
                self.log_queue.task_done()
                
            except Exception as e:
                print(f"❌ Errore worker log: {e}")
                time.sleep(5)

    def get_stats(self):
        """Recupera statistiche reali dal database."""
        if not self.is_initialized:
            return {"users": 0, "detections": 0, "people": 0, "others": 0}
            
        async def _stats_task():
            try:
                user_count = await User.count()
                det_count = await Detection.count()
                
                # Aggregazione per contare persone e altri oggetti
                pipeline = [
                    {"$unwind": "$objects"},
                    {"$group": {
                        "_id": None,
                        "people": {"$sum": {"$cond": [
                            {"$or": [
                                {"$eq": ["$objects.label", "person"]},
                                {"$eq": ["$objects.class", "person"]}
                            ]}, 1, 0]}},
                        "others": {"$sum": {"$cond": [
                            {"$and": [
                                {"$ne": ["$objects.label", "person"]},
                                {"$ne": ["$objects.class", "person"]}
                            ]}, 1, 0]}}
                    }}
                ]
                
                # Usa direttamente motor per l'aggregazione per evitare ambiguità con Beanie
                coll = self.db.get_collection("detections")
                cursor = coll.aggregate(pipeline)
                agg_results = await cursor.to_list(length=1)
                stats = agg_results[0] if agg_results else {"people": 0, "others": 0}

                return {
                    "users": user_count, 
                    "detections": det_count, 
                    "people": stats.get("people", 0), 
                    "others": stats.get("others", 0)
                }
            except Exception as e:
                print(f"❌ Errore _stats_task: {e}")
                return {"users": 0, "detections": 0, "people": 0, "others": 0}

        future = asyncio.run_coroutine_threadsafe(_stats_task(), self.loop)
        try:
            return future.result(timeout=5)
        except:
            return {"users": 0, "detections": 0, "people": 0, "others": 0}

    def get_detections(self, limit=100, class_filter=None):
        """Recupera la lista dei rilevamenti con possibilità di filtro."""
        if not self.is_initialized:
            return []
            
        async def _get_task():
            query = {}
            if class_filter:
                query = {"$or": [
                    {"objects.label": class_filter},
                    {"objects.class": class_filter}
                ]}
            
            return await Detection.find(query).sort("-timestamp").limit(limit).to_list()

        future = asyncio.run_coroutine_threadsafe(_get_task(), self.loop)
        try:
            return future.result(timeout=5)
        except:
            return []

    def clear_all_logs(self):
        """Elimina tutti i rilevamenti dal database."""
        if not self.is_initialized:
            return False, "Database non pronto"

        async def _clear_task():
            try:
                await Detection.find_all().delete()
                return True, "Tutti i log eliminati correttamente"
            except Exception as e:
                return False, str(e)

        future = asyncio.run_coroutine_threadsafe(_clear_task(), self.loop)
        try:
            return future.result(timeout=10)
        except Exception as e:
            return False, f"Errore eliminazione: {e}"

    def delete_log(self, log_id):
        """Elimina un singolo rilevamento dal database."""
        if not self.is_initialized:
            return False, "Database non pronto"

        async def _delete_task():
            try:
                # Se log_id è una stringa, convertilo in PydanticObjectId
                if isinstance(log_id, str):
                    obj_id = PydanticObjectId(log_id)
                else:
                    obj_id = log_id
                    
                log = await Detection.get(obj_id)
                if log:
                    await log.delete()
                    return True, "Log eliminato correttamente"
                return False, "Log non trovato"
            except Exception as e:
                return False, str(e)

        future = asyncio.run_coroutine_threadsafe(_delete_task(), self.loop)
        try:
            return future.result(timeout=10)
        except Exception as e:
            return False, f"Errore eliminazione: {e}"

    def close(self):
        self.is_running = False
        if self.loop:
            self.loop.call_soon_threadsafe(self.loop.stop)
