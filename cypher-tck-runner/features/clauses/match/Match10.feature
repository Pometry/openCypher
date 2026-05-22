#encoding: utf-8

Feature: Match10 - Expand to unlabeled node (NodeLabelId wildcard)

  Scenario: [1] Match labeled node expanding to unlabeled node (undirected)
    Given an empty graph
    And having executed:
      """
      CREATE (:City {name: 'Rome'})-[:IS_LOCATED_IN]->({name: 'Italy'})
      """
    When executing query:
      """
      MATCH (o)-[:IS_LOCATED_IN]-(c :City)
      RETURN o.name
      """
    Then the result should be, in any order:
      | o.name  |
      | 'Italy' |
    And no side effects

  Scenario: [2] Match labeled node with property filter expanding to unlabeled node
    Given an empty graph
    And having executed:
      """
      CREATE (:City {name: 'Rome', code: 'IT-RM'})-[:IS_LOCATED_IN]->({name: 'Italy'})
      """
    And having executed:
      """
      CREATE (:City {name: 'Paris', code: 'FR-PA'})-[:IS_LOCATED_IN]->({name: 'France'})
      """
    When executing query:
      """
      MATCH (o)-[:IS_LOCATED_IN]-(c :City)
      WHERE c.code = 'IT-RM'
      RETURN o.name
      """
    Then the result should be, in any order:
      | o.name  |
      | 'Italy' |
    And no side effects

  Scenario: [3] Match directed edge from labeled to unlabeled node
    Given an empty graph
    And having executed:
      """
      CREATE (:Person {name: 'Alice'})-[:KNOWS]->({name: 'Bob'})
      """
    When executing query:
      """
      MATCH (p :Person)-[:KNOWS]->(o)
      RETURN o.name
      """
    Then the result should be, in any order:
      | o.name |
      | 'Bob'  |
    And no side effects

  Scenario: [4] Match directed edge from unlabeled to labeled node
    Given an empty graph
    And having executed:
      """
      CREATE ({name: 'Bob'})-[:KNOWS]->(:Person {name: 'Alice'})
      """
    When executing query:
      """
      MATCH (o)-[:KNOWS]->(p :Person)
      RETURN o.name
      """
    Then the result should be, in any order:
      | o.name |
      | 'Bob'  |
    And no side effects
