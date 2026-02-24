# Feature: Mark Todo as Done

> This is a reference example. Use this format for your own specs.

## Overview
Users can mark a todo as completed by its ID.

## User Story
As a CLI user, I want to mark todos as done so that I can track my progress.

## Acceptance Criteria

### AC1: Mark existing todo as done
**Given** a todo with id 1 exists and is not completed
**When** the user runs `done 1`
**Then** the todo's completed field is set to true
**And** the CLI outputs: "Completed todo #1: Buy groceries"

### AC2: Mark already-completed todo
**Given** a todo with id 1 exists and is already completed
**When** the user runs `done 1`
**Then** the todo remains completed
**And** the CLI outputs: "Todo #1 is already done"

### AC3: Invalid ID
**Given** no todo with id 999 exists
**When** the user runs `done 999`
**Then** no changes are made
**And** the CLI outputs: "Todo #999 not found"

### AC4: Non-numeric ID
**Given** any state
**When** the user runs `done abc`
**Then** the CLI outputs: "Invalid ID. Use a number."

## Technical Constraints
- Modify the todo in-place in the storage array
- Return the updated todo object from the business logic function

## Test Strategy
- Unit tests for each AC
- Verify storage state after each operation
