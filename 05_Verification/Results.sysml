// Target spec: SysML v2 2025-07 (SysIDE 0.8.x compatible)
/**
 * Results — shared result item definitions.
 *
 * LEAF FILE.  Globally unique name "Results".
 *
 * TestResult is kept as a passive data item def for documentation
 * and potential future use (e.g. storing summary results from a
 * completed program milestone as a model snapshot).
 *
 * Live test results are NOT stored in the model. The result_matrix.py
 * tool reads results from CTest JUnit XML output and joins against
 * verification names declared in the model.
 */
package Results {
    private import ScalarValues::*;

    item def TestResult {
        doc /* Outcome record — for milestone snapshots only, not live results. */
        attribute passed  : Boolean;
        attribute summary : String;
    }
}
