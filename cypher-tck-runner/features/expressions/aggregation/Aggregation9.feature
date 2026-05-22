#encoding: utf-8

Feature: Aggregation9 - collect(DISTINCT ...) with labels and duplicates

  Scenario: [1] Return unique labels as a collection using UNWIND
    Given an empty graph
    And having executed:
      """
      CREATE (:A), (:A), (:B), (:A:B)
      """
    When executing query:
      """
      MATCH (n)
      UNWIND labels(n) AS label
      RETURN collect(DISTINCT label) AS labels
      """
    Then the result should be, in any order:
      | labels     |
      | ['A', 'B'] |
    And no side effects

  Scenario: [2] collect(DISTINCT ...) removes duplicates from UNWIND list
    Given any graph
    When executing query:
      """
      UNWIND ['a', 'b', 'a', 'c', 'b'] AS x
      RETURN collect(DISTINCT x) AS result
      """
    Then the result should be, in any order:
      | result          |
      | ['a', 'b', 'c'] |
    And no side effects

  Scenario: [3] collect(DISTINCT ...) on a list with no duplicates returns all values
    Given any graph
    When executing query:
      """
      UNWIND [1, 2, 3] AS x
      RETURN collect(DISTINCT x) AS result
      """
    Then the result should be, in any order:
      | result    |
      | [1, 2, 3] |
    And no side effects

  Scenario: [4] collect(DISTINCT ...) on empty input returns empty list
    Given an empty graph
    When executing query:
      """
      MATCH (n)
      UNWIND labels(n) AS label
      RETURN collect(DISTINCT label) AS result
      """
    Then the result should be, in any order:
      | result |
      | []     |
    And no side effects

  Scenario: [5] collect(DISTINCT ...) with integer duplicates
    Given any graph
    When executing query:
      """
      UNWIND [1, 2, 1, 3, 2, 1] AS x
      RETURN collect(DISTINCT x) AS result
      """
    Then the result should be, in any order:
      | result    |
      | [1, 2, 3] |
    And no side effects
