#encoding: utf-8

Feature: Match12 - Pattern predicate in WHERE clause (EXISTS / NOT EXISTS)

  Scenario: [1] NOT pattern predicate filters out nodes with matching pattern
    Given an empty graph
    And having executed:
      """
      CREATE (:University {name: 'MIT'})-[:IS_LOCATED_IN]->(:City {name: 'Boston'})
      """
    And having executed:
      """
      CREATE (:University {name: 'Oxford'})-[:IS_LOCATED_IN]->(:City {name: 'London'})
      """
    And having executed:
      """
      CREATE (:University {name: 'Standalone'})
      """
    When executing query:
      """
      MATCH (u:University)
      WHERE NOT (u)-[:IS_LOCATED_IN]-(:City {name: 'Boston'})
      RETURN u.name
      """
    Then the result should be, in any order:
      | u.name       |
      | 'Oxford'     |
      | 'Standalone' |
    And no side effects

  Scenario: [2] Positive pattern predicate keeps only nodes with matching pattern
    Given an empty graph
    And having executed:
      """
      CREATE (:University {name: 'MIT'})-[:IS_LOCATED_IN]->(:City {name: 'Boston'})
      """
    And having executed:
      """
      CREATE (:University {name: 'Oxford'})-[:IS_LOCATED_IN]->(:City {name: 'London'})
      """
    And having executed:
      """
      CREATE (:University {name: 'Standalone'})
      """
    When executing query:
      """
      MATCH (u:University)
      WHERE (u)-[:IS_LOCATED_IN]-(:City {name: 'Boston'})
      RETURN u.name
      """
    Then the result should be, in any order:
      | u.name |
      | 'MIT'  |
    And no side effects

  Scenario: [3] NOT pattern predicate with multi-pattern MATCH
    Given an empty graph
    And having executed:
      """
      CREATE (:Person {name: 'Alice'})-[:STUDIES_AT]->(:University {name: 'MIT'})-[:IS_LOCATED_IN]->(:City {name: 'Boston'})
      """
    And having executed:
      """
      CREATE (:Person {name: 'Bob'})-[:STUDIES_AT]->(:University {name: 'Oxford'})-[:IS_LOCATED_IN]->(:City {name: 'London'})
      """
    When executing query:
      """
      MATCH (m:Person)-[:STUDIES_AT]->(o:University)
      WHERE NOT (o)-[:IS_LOCATED_IN]-(:City {name: 'Boston'})
      RETURN m.name
      """
    Then the result should be, in any order:
      | m.name |
      | 'Bob'  |
    And no side effects

  Scenario: [4] NOT pattern predicate returns all rows when no node matches the inner pattern
    Given an empty graph
    And having executed:
      """
      CREATE (:University {name: 'MIT'})
      """
    And having executed:
      """
      CREATE (:University {name: 'Oxford'})
      """
    When executing query:
      """
      MATCH (u:University)
      WHERE NOT (u)-[:IS_LOCATED_IN]-(:City {name: 'Boston'})
      RETURN u.name
      """
    Then the result should be, in any order:
      | u.name   |
      | 'MIT'    |
      | 'Oxford' |
    And no side effects
