---
title: Sales data-quality runbook
owner: Data platform team (fictional)
synthetic: true
---

# Sales data-quality runbook

> SYNTHETIC DOCUMENT. Fictional manufacturer runbook written for education. Not real guidance.

## Detection

Silver rules detect duplicate order lines, negative quantities, missing customers, unknown
products, future order dates, inconsistent region names and prices far outside the list price.
Detection is automatic and runs on every load.

## Correction

Agents and notebooks may propose a correction, but they never change the source records. A data
steward reviews each proposal. Approved fixes are applied in the source system or as a governed
Silver rule change through the change flow: plan, approve, execute, verify and audit.

## Duplicates

A duplicate is an order line with the same order number, line number, product and quantity as an
earlier line. The earlier line is kept and the later copy is flagged.
