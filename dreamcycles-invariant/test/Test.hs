module Main where

import DreamcyclesInvariant

main :: IO ()
main = do
  putStrLn "=== DreamcyclesInvariant Test Suite ==="

  -- Test 1: preservesInvariant (exact match)
  let x = 42 :: Int
  let result = preservesInvariant id (+ 1) id x
  case result of
    Verified v InvariantPreserved -> putStrLn $ "PASS: invariant preserved (got " ++ show v ++ ")"
    _ -> putStrLn "FAIL: invariant should be preserved"

  -- Test 2: preservesInvariant (violation)
  let result2 = preservesInvariant (* 2) (+ 1) id (10 :: Int)
  case result2 of
    Refuted _ msg -> putStrLn $ "PASS: invariant violated (" ++ msg ++ ")"
    _ -> putStrLn "FAIL: should detect violation"

  -- Test 3: preservesInvariantMetric
  let cx = (1.0 :+ 0.0) :: Amp
  let result3 = preservesInvariantMetric
        (\_ -> cx)
        (+ 1)
        (\_ -> cx)
        (0 :: Int)
        (\a b -> magnitude (a - b))
        0.01
  case result3 of
    Verified _ InvariantPreserved -> putStrLn "PASS: metric invariant preserved"
    _ -> putStrLn "FAIL: metric invariant should hold"

  -- Test 4: deferVerification
  let result4 = deferVerification (+ 1) (5 :: Int)
  case result4 of
    Unverified msg -> putStrLn $ "PASS: deferred (" ++ msg ++ ")"
    _ -> putStrLn "FAIL: should be unverified"

  -- Test 5: semanticallyEquivalent
  let result5 = semanticallyEquivalent (+ 0) (7 :: Int)
  case result5 of
    Verified v SemanticEquivalent -> putStrLn $ "PASS: semantic eq (got " ++ show v ++ ")"
    _ -> putStrLn "FAIL: should be semantically equivalent"

  -- Test 6: Quantum superposition
  let q0 = mkQubit [(1.0 :+ 0.0, False)]
  let qH = hadamard q0
  putStrLn $ "H|0> = " ++ showQubit qH
  let p = totalProb qH
  putStrLn $ "Total probability: " ++ show p
  if abs (p - 1.0) < 1e-10
    then putStrLn "PASS: probability conserved"
    else putStrLn "FAIL: probability should be 1.0"

  -- Test 7: TensorBlock
  let tb = TensorBlock [1, 2, 3, 4, 5]
  let tb2 = foldTensor (filter (> 3)) tb
  putStrLn $ "Filtered tensor: " ++ show tb2
  if tbLength tb2 == 2
    then putStrLn "PASS: foldTensor works"
    else putStrLn "FAIL: foldTensor incorrect"

  putStrLn "=== All tests complete ==="
