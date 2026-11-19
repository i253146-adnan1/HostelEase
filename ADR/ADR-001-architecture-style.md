# ADR-001: Layered Monolithic Architecture

**Status:** Accepted

## Context
HostelEase ek single-warden hostel management system hai, koi external 
payment integration nahi (C-01), koi technology/hosting pehle se decide 
nahi thi (C-04). Scale chhota hai: ek admin (warden) + students ki limited 
population. Dashboard ko 3 modules (fee, complaints, rooms) se data 
aggregate karke 3-second response dena hai (NFR-04, FR-14). In drivers ko 
dekhte hue overall architectural style decide karni thi.

## Alternatives considered
1. **Layered monolith** — ek codebase, presentation/business-logic/data 
   layers alag.
2. **Modular monolith** — ek deploy unit, har feature apna isolated module/folder.
3. **Microservices** — har module (fee, rooms, complaints, etc.) alag deployable service.

## Decision
Layered monolith adopt kiya — single deployable application, teen layers 
mein organized: presentation (UI/routes), business logic (services per 
feature), data access (DB models/queries).

## Rationale
- Scale justify nahi karta distributed system ki complexity (single warden, 
  course-project traffic).
- Microservices deployment/ops overhead laate hain jo koi ASR demand nahi 
  karta — C-04 (no tech specified) sirf freedom deta hai, zarurat nahi.
- Modular monolith zyada upfront folder/module discipline maangta hai jo 
  is team size (4 members, 6-day window) ke liye avoidable overhead hai.
- Layered style fir bhi FR/NFR satisfy karta hai: layers ke beech clear 
  separation se Auth Guard cross-cutting concern ke tor pe implement ho 
  sakta hai, aur Dashboard business-logic layer se hi read-only aggregation 
  kar sakta hai bina apna data model rakhe.

## Trade-offs / Consequences
- (+) Simple setup, ek hi codebase, deploy karna aasan, demo ke liye 
  samajhna/explain karna aasan.
- (+) AI coding agent ke liye clear, predictable structure follow karna 
  easy hoga (Deliverable-3 ka core goal).
- (−) Agar future mein scale badhta (zyada wardens/hostels), is style ko 
  refactor karna padega — abhi ke liye acceptable risk, NG/scope se bahar hai.
- (−) Strict module boundaries enforce karne ke liye discipline chahiye 
  (koi module directly dusre ki table na chhue) — isko AGENTS.md mein 
  explicit rule banana zaroori hai.