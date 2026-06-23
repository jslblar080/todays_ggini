"""
FILE: src/db/graph_store.py
ROLE: 본질(Ingredient Node)과 상태(Relationship Property)를 분리하여 저장.
"""
from neo4j import GraphDatabase
from src.processor.models import RecipeSchema

class GraphStore:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def save_recipe(self, recipe: RecipeSchema):
        with self.driver.session() as session:
            session.execute_write(self._create_recipe_nodes, recipe)

    @staticmethod
    def _create_recipe_nodes(tx, recipe: RecipeSchema):
        query = """
        MERGE (m:Menu {name: $menu_name})
        SET m.category = $category, m.instructions = $instructions
        WITH m
        UNWIND $ingredients AS ing
        MERGE (i:Ingredient {name: ing.base_name})  // 여기서 노드 통합 발생
        MERGE (m)-[r:REQUIRES]->(i)
        SET r.state = ing.state,
            r.raw_name = ing.raw_name,
            r.numeric_value = ing.numeric_value,
            r.unit = ing.unit
        """
        ings_dict = [ing.model_dump() for ing in recipe.ingredients]
        tx.run(query, 
               menu_name=recipe.menu_name, 
               category=recipe.category, 
               instructions=recipe.instructions, 
               servings=recipe.servings, 
               ingredients=ings_dict)