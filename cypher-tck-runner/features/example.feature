#
# Example feature file for testing the TCK runner setup
#

Feature: Example - Basic query operations

  Scenario: [1] Return a simple value
    Given an empty graph
    When executing query:
      """
      RETURN 1 AS value
      """
    Then the result should be, in any order:
      | value |
      | 1     |
    And no side effects

  Scenario: [2] Create a single node
    Given an empty graph
    When executing query:
      """
      CREATE ()
      """
    Then the result should be empty
    And the side effects should be:
      | +nodes | 1 |

  Scenario: [3] Match in empty graph returns empty
    Given an empty graph
    When executing query:
      """
      MATCH (n)
      RETURN n
      """
    Then the result should be, in any order:
      | n |
    And no side effects
