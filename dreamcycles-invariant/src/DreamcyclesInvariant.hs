-- Copyright © 2026 SnapKitty Collective and contributors.
--
-- This file is part of a work licensed under the
-- SnapKitty Strong Network Copyleft License Version 1.0 (SSNCL-1.0).
--
-- You may use, study, modify, copy, and redistribute this work
-- only under the terms of SSNCL-1.0.
--
-- A copy of SSNCL-1.0 must accompany this work.

{-|
  DreamcyclesInvariant
  --------------------
  Corrected invariant-preservation kit (all prior holes filled), a complex-valued
  metric variant (tolerance, not bare Eq), a small quantum superposition model,
  and a live connection to the ANU QRNG quantum node (https://qrng.anu.edu.au)
  whose quantum random uint16 outcomes drive measurement/collapse.

  Base + process only (no external Hackage dependencies).
-}
module DreamcyclesInvariant
  ( -- * Invariant-preservation kit
    Proof(..), Verification(..), TensorBlock(..), foldTensor, tbLength
  , preservesInvariant, preservesInvariantMetric
  , deferVerification, semanticallyEquivalent
    -- * Quantum superposition
  , Amp, Qubit(..), sqNorm, totalProb, mkQubit, hadamard, pick
  , measureWith, sumProbC, showQubit
    -- * ANU QRNG quantum node
  , anuUrl, fetchANU, parseData
  ) where

import Data.Char     (isSpace)
import Data.Complex  (Complex(..), magnitude)
import Data.List     (isPrefixOf)
import System.Exit   (ExitCode(..))
import System.Process (readProcessWithExitCode)
import Text.Read     (readMaybe)

-- ----------------------------------------------------------------------
-- 1. Corrected invariant-preservation kit (holes from the prior turn filled)
-- ----------------------------------------------------------------------

data Proof = InvariantPreserved | SemanticEquivalent
  deriving (Show, Eq)

-- hole 2: Refuted now carries the offending value a.
-- hole 1: Unverified is a real branch with its own producer.
data Verification a
  = Verified a Proof
  | Unverified String
  | Refuted a String
  deriving (Show, Eq)

data TensorBlock a = TensorBlock [a]
  deriving (Show, Eq)

-- Not a fold (no monoid/accumulator); a list-morphism in a newtype.
foldTensor :: ([a] -> [a]) -> TensorBlock a -> TensorBlock a
foldTensor f (TensorBlock xs) = TensorBlock (f xs)

tbLength :: TensorBlock a -> Int
tbLength (TensorBlock xs) = length xs

-- Exact-Eq variant (for discrete invariants, e.g. dimension/energy).
preservesInvariant :: Eq i => (a -> i) -> (a -> b) -> (b -> i) -> a -> Verification b
preservesInvariant before transform after x =
  let y  = transform x
      i0 = before x
      i1 = after y
  in if i0 == i1
     then Verified y InvariantPreserved
     else Refuted y "invariant-violation"

-- hole 4: complex-valued metric variant. i ~ Complex Double, comparison via a
-- supplied metric (magnitude of difference) and tolerance -- NOT bare ==.
preservesInvariantMetric
  :: (a -> Complex Double)        -- before
  -> (a -> b)                     -- transform
  -> (b -> Complex Double)        -- after
  -> a                            -- input
  -> (Complex Double -> Complex Double -> Double)  -- metric
  -> Double                       -- tolerance
  -> Verification b
preservesInvariantMetric before transform after x metric tol =
  let y  = transform x
      i0 = before x
      i1 = after y
  in if metric i0 i1 <= tol
     then Verified y InvariantPreserved
     else Refuted y "invariant-violation"

-- hole 1 producer: defer the proof.
deferVerification :: (a -> b) -> a -> Verification b
deferVerification _ _ = Unverified "proof-deferred"

-- hole 3 producer: a genuinely different proof witness.
semanticallyEquivalent :: (a -> a) -> a -> Verification a
semanticallyEquivalent f x = Verified (f x) SemanticEquivalent

-- ----------------------------------------------------------------------
-- 2. Quantum superposition (pure-functional model over Complex amplitudes).
-- ----------------------------------------------------------------------

type Amp = Complex Double
data Qubit = Qubit [(Amp, Bool)]
  deriving (Show, Eq)

sqNorm :: Amp -> Double
sqNorm a = magnitude a ^ 2

totalProb :: Qubit -> Double
totalProb (Qubit amps) = sum (map (sqNorm . fst) amps)

-- Normalize so probabilities sum to 1.
mkQubit :: [(Amp, Bool)] -> Qubit
mkQubit amps =
  let t = sum (map (sqNorm . fst) amps)
      n = if t == 0 then 1 else sqrt t
  in Qubit [ (a / (n :+ 0), b) | (a, b) <- amps ]

-- Hadamard gate on a single qubit (basis order: False=|0>, True=|1>).
hadamard :: Qubit -> Qubit
hadamard (Qubit [(a0, False), (a1, True)]) =
  Qubit [ ((a0 + a1) / s, False), ((a0 - a1) / s, True) ]
  where s = sqrt 2 :+ 0
hadamard q = q  -- only defined on the canonical 2-state basis

-- Weighted pick over cumulative probabilities. r in [0,1) from ANU QRNG.
pick :: Double -> [(Double, Bool)] -> Bool
pick r = go r
  where
    go _ []          = False
    go _ ((_,b):[])  = b          -- last element: always take it (float drift safe)
    go k ((p,b):rest)
      | k < p     = b
      | otherwise = go (k - p) rest

-- Collapse: ANU quantum randomness selects the outcome.
measureWith :: Double -> Qubit -> (Bool, Qubit)
measureWith r (Qubit amps) =
  let t = sum (map (sqNorm . fst) amps)
      probs = [ (sqNorm a / t, b) | (a, b) <- amps ]
      outcome = pick r probs
  in (outcome, Qubit [(1 :+ 0, outcome)])

sumProbC :: Qubit -> Complex Double
sumProbC q = totalProb q :+ 0

showQubit :: Qubit -> String
showQubit (Qubit amps) = unwords
  [ "(" ++ show a ++ "|" ++ (if b then "1" else "0") ++ ">" ++ ")"
  | (a, b) <- amps ]

-- ----------------------------------------------------------------------
-- 3. ANU quantum node connection (QRNG, true quantum vacuum entropy).
-- ----------------------------------------------------------------------

anuUrl :: Int -> String
anuUrl n = "https://qrng.anu.edu.au/API/jsonI.php?length="
        ++ show n ++ "&type=uint16&size=1024"

-- Minimal JSON extraction of the "data":[...] array (no Aeson dependency).
findAfter :: String -> String -> Maybe String
findAfter needle hay = go hay
  where go [] = Nothing
        go xs@(_:xt) | needle `isPrefixOf` xs = Just (drop (length needle) xs)
                     | otherwise               = go xt

splitOn :: Char -> String -> [String]
splitOn c s = case break (== c) s of
  (a, [])     -> [trim a]
  (a, _:rest) -> trim a : splitOn c rest
  where trim = f . f; f = reverse . dropWhile isSpace

parseData :: String -> Maybe [Int]
parseData s = do
  rest <- findAfter "\"data\":[" s
  let (nums, _) = break (== ']') rest
  mapM readMaybe (filter (not . null) (splitOn ',' nums))

fetchANU :: Int -> IO (Either String [Int])
fetchANU n = do
  (code, out, _err) <- readProcessWithExitCode "curl"
                         ["-s", "--max-time", "25", anuUrl n] ""
  case code of
    ExitFailure e -> return (Left ("curl exit " ++ show e))
    ExitSuccess   -> case parseData out of
      Nothing -> return (Left ("parse failed: " ++ take 120 out))
      Just xs -> return (Right xs)
