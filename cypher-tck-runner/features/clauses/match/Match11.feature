#encoding: utf-8

Feature: Match11 - Multi-pattern MATCH with shared variable

  Scenario: [1] Multi-pattern MATCH chains on shared variable
    Given an empty graph
    And having executed:
      """
      CREATE (:Person {name: 'Alice'})-[:STUDIES_AT]->(:University {name: 'MIT'})-[:IS_LOCATED_IN]->(:City {name: 'Boston'})
      """
    And having executed:
      """
      CREATE (:Person {name: 'Bob'})-[:STUDIES_AT]->(:University {name: 'Harvard'})-[:IS_LOCATED_IN]->(:City {name: 'Boston'})
      """
    And having executed:
      """
      CREATE (:Person {name: 'Carol'})-[:STUDIES_AT]->(:University {name: 'Oxford'})-[:IS_LOCATED_IN]->(:City {name: 'London'})
      """
    When executing query:
      """
      MATCH (m:Person)-[:STUDIES_AT]->(o:University), (o)-[:IS_LOCATED_IN]->(c:City)
      WHERE c.name = 'Boston'
      RETURN m.name
      """
    Then the result should be, in any order:
      | m.name  |
      | 'Alice' |
      | 'Bob'   |
    And no side effects

  Scenario: [2] Multi-pattern MATCH does not cross-join unrelated combinations
    Given an empty graph
    And having executed:
      """
      CREATE (:Person {name: 'Alice'})-[:STUDIES_AT]->(:University {name: 'MIT'})-[:IS_LOCATED_IN]->(:City {name: 'Boston'})
      """
    And having executed:
      """
      CREATE (:University {name: 'Oxford'})-[:IS_LOCATED_IN]->(:City {name: 'London'})
      """
    When executing query:
      """
      MATCH (m:Person)-[:STUDIES_AT]->(o:University), (o)-[:IS_LOCATED_IN]->(c:City)
      RETURN m.name, o.name, c.name
      """
    Then the result should be, in any order:
      | m.name  | o.name | c.name   |
      | 'Alice' | 'MIT'  | 'Boston' |
    And no side effects

  Scenario: [3] Multi-pattern MATCH with undirected first pattern
    Given an empty graph
    And having executed:
      """
      CREATE (:Person {name: 'Alice'})-[:MEMBER_OF]->(:University {name: 'MIT'})-[:IS_LOCATED_IN]->(:City {name: 'Boston'})
      """
    When executing query:
      """
      MATCH (m:Person)-[]-(o:University), (o)-[:IS_LOCATED_IN]-(c:City)
      RETURN m.name, c.name
      """
    Then the result should be, in any order:
      | m.name  | c.name   |
      | 'Alice' | 'Boston' |
    And no side effects

  Scenario: [4] Multi-pattern MATCH returns no results when shared variable has no matching second pattern
    Given an empty graph
    And having executed:
      """
      CREATE (:Person {name: 'Alice'})-[:STUDIES_AT]->(:University {name: 'MIT'})
      """
    And having executed:
      """
      CREATE (:University {name: 'Oxford'})-[:IS_LOCATED_IN]->(:City {name: 'London'})
      """
    When executing query:
      """
      MATCH (m:Person)-[:STUDIES_AT]->(o:University), (o)-[:IS_LOCATED_IN]->(c:City)
      RETURN m.name
      """
    Then the result should be, in any order:
      | m.name |
    And no side effects
