from abc import ABC, abstractmethod
from typing import Generic, TypeVar
from pydantic import BaseModel
T=TypeVar("T",bound=BaseModel)
class Repository(ABC,Generic[T]):
 @abstractmethod
 def get(self,item_id:str)->T|None:...
 @abstractmethod
 def list(self)->list[T]:...
 @abstractmethod
 def upsert(self,item:T)->T:...
class MemoryRepository(Repository[T]):
 def __init__(self): self.items={}
 def get(self,item_id): return self.items.get(item_id)
 def list(self): return list(self.items.values())
 def upsert(self,item): self.items[item.id]=item; return item
class FirestoreRepository(Repository[T]):
 def __init__(self,collection,model,client): self.collection=client.collection(collection); self.model=model
 def get(self,item_id):
  doc=self.collection.document(item_id).get()
  if not doc.exists:return None
  return self.model.model_validate({**doc.to_dict(),"id":doc.id})
 def list(self): return [self.model.model_validate({**d.to_dict(),"id":d.id}) for d in self.collection.stream()]
 def upsert(self,item): self.collection.document(item.id).set(item.model_dump(mode="json")); return item
class RepositorySet:
 def __init__(self,r): self.__dict__.update(r)
