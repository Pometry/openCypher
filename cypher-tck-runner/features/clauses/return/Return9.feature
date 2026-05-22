#encoding: utf-8

Feature: Return9 - Quoted alias compatibility (single/double quotes as AS alias)

  Scenario: [1] Single-quoted alias is accepted and applied
    Given an empty graph
    And having executed:
      """
      CREATE (:Person {name: 'Alice'})
      """
    When executing query:
      """
      MATCH (n:Person)
      RETURN n.name AS 'person_name'
      """
    Then the result should be, in any order:
      | person_name |
      | 'Alice'     |
    And no side effects

  Scenario: [2] All return items are returned when some aliases are quoted
    Given an empty graph
    And having executed:
      """
      CREATE (:A {x: 1})-[:REL]->(:B {x: 2})
      """
    When executing query:
      """
      MATCH (n)-[r]->(m)
      RETURN n.x AS 'n_x', type(r) AS r_type, m.x AS 'm_x'
      """
    Then the result should be, in any order:
      | n_x | r_type | m_x |
      | 1   | 'REL'  | 2   |
    And no side effects

  Scenario: [3] Multiple quoted aliases are all applied correctly
    Given an empty graph
    And having executed:
      """
      CREATE (:Person {name: 'Bob', age: 25})
      """
    When executing query:
      """
      MATCH (n:Person)
      RETURN n.name AS 'person_name', n.age AS 'person_age'
      """
    Then the result should be, in any order:
      | person_name | person_age |
      | 'Bob'       | 25         |
    And no side effects

  Scenario: [4] Quoted alias in WITH clause is accepted and applied
    Given an empty graph
    And having executed:
      """
      CREATE (:Person {age: 30})
      """
    When executing query:
      """
      MATCH (n:Person)
      WITH n.age AS 'person_age'
      RETURN person_age
      """
    Then the result should be, in any order:
      | person_age |
      | 30         |
    And no side effects
