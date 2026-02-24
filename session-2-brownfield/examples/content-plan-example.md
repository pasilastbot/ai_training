# Documentation Content Plan — Example

> This is a reference example for a hypothetical e-commerce app.
> Use this format when creating your content-plan.md for Suroi.

## Overview
E-commerce platform with product catalog, shopping cart, checkout, and order management. Built with Next.js, TypeScript, and PostgreSQL.

## Documentation Index

| # | Module | Status | Path | Priority |
|---|--------|--------|------|----------|
| 1 | Architecture Overview | Done | `docs/architecture.md` | Critical |
| 2 | Authentication System | Done | `docs/auth-system.md` | Critical |
| 3 | Product Catalog | In Progress | `docs/product-catalog.md` | High |
| 4 | Shopping Cart | Not Started | `docs/shopping-cart.md` | High |
| 5 | Checkout Flow | Not Started | `docs/checkout.md` | High |
| 6 | Order Management | Not Started | `docs/order-management.md` | Medium |
| 7 | Payment Processing | Not Started | `docs/payments.md` | Medium |
| 8 | Notification System | Not Started | `docs/notifications.md` | Low |
| 9 | Admin Dashboard | Not Started | `docs/admin.md` | Low |

## Generation Instructions

Generate docs in this order:
1. Architecture overview first (dependencies, data flow, deployment)
2. Core systems next (auth, products — these are dependencies for everything else)
3. Feature modules (cart, checkout, orders)
4. Supporting systems last (notifications, admin)

Each doc should include:
- Purpose and scope
- Key files and entry points (with @file references)
- Data flow (how data moves through the module)
- Dependencies on other modules
- Known issues or tech debt
