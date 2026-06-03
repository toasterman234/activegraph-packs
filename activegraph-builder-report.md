# Building with ActiveGraph: A Developer's Field Report

**Package:** `activegraph` v1.0.5.post2 (PyPI)  
**Context:** Built a full pack library (identity, memory-gateway, comm-processor, email, calendar packs), a Python HTTP demo server, an Express proxy API, and a React Inspector UI against a live runtime.  
**Author:** Replit Agent — honest account, warts and all.

---

## What ActiveGraph Is (And Isn't)

ActiveGraph is a **reactive object graph runtime** for Python. You define *objects* (typed nodes in a graph), *relations* (typed edges between them), *behaviors* (reactive handlers that fire when objects are added or updated), and *tools* (callable capabilities packs expose). Packs are the unit of composition — each pack owns a namespace, registers its schemas, and wires its behaviors into the runtime.

It is **not** a framework in the Rails/Django sense. There's no HTTP server and no ORM — but it *does* ship a durable persistence layer (a pluggable, event-sourced store with SQLite and Postgres backends; more on that below). It's closer to a low-level reactive engine: you build your domain logic in packs, wire packs into a runtime, and the runtime takes care of cascading behaviors and graph state. What you do with that state is entirely up to you.

The closest analogies are:
- **Datalog engines** (Datomic, XTDB) — because ActiveGraph is essentially a reactive triple store with triggers
- **ECS (Entity Component System)** from game engines — packs are systems, objects are entities, relations are components
- **Actor model** runtimes — because behaviors are reactive and fire asynchronously in response to state changes

It is decidedly **not** like LangChain, AutoGen, or CrewAI. Those frameworks focus on orchestrating LLM calls with predefined workflow graphs. ActiveGraph doesn't know what an LLM is — it's the substrate *below* LLM calls. You use ActiveGraph to represent agent memory, identity, context, and actions as a live graph, then bolt LLM calls onto behaviors as one implementation detail among many.

---

## The Core Mental Model

The mental model that clicks once you get it:

```
Pack = namespace + schemas + behaviors + tools
Runtime = graph engine + behavior dispatcher
Graph = live object store (opt-in SQLite/Postgres persistence via built-in store)

graph.add_object(type, data) → fires behavior chain
rt.run_until_idle()           → drains all cascading reactions
graph.get_object(id)          → point lookup (safe in behaviors)
graph.objects()               → full scan (UNSAFE in behaviors — re-entrant)
```

Everything flows from `add_object`. Adding a `core/source` might trigger a `principal_resolver` behavior that adds an `identity_auth/principal`, which triggers an `auth_context_builder` behavior, which adds a `core/observation`. The full cascade is synchronous within `run_until_idle()` but feels asynchronous to write.

This is genuinely elegant once it clicks. Your domain logic decomposes into small, single-responsibility behaviors rather than monolithic pipelines.

---

## Developer Experience: The Honest Version

### What Works Well

**Pack isolation is real.** Each pack genuinely owns its namespace. If you name your types `my_pack/my_type`, there's no collision with other packs. The import surface is narrow: inherit from `Pack`, decorate your methods, register your schemas. This makes multi-pack systems composable in a way that LangChain chains aren't — you can drop in or remove a pack without touching others.

**The behavior cascade is powerful.** Writing a chain that goes `email_received → extract_sender → resolve_principal → build_auth_context → evaluate_permissions` as five separate `@behavior` handlers is more maintainable than one 200-line function. Each behavior is independently testable. The cascade is deterministic. Debugging is straightforward: you can trace which object triggered which behavior in sequence.

**Schema-as-data is useful.** Defining object schemas as class attributes with type annotations means your graph is self-describing. The Inspector UI was able to enumerate object types, count instances per type, and display structured fields without any hand-rolled serialization — it just asked the runtime what it knew.

**The runtime is fast enough to not think about.** Seeding 18 objects and 102 events happens in milliseconds. The graph projection is held in-memory and behaviors fire synchronously, so reads have no I/O overhead. When you attach a persistence backend, the runtime appends events to the store as they happen; for a demo server or test harness, this is excellent.

**It's pure Python.** No Rust extensions, no native deps, no platform-specific installation quirks. `pip install activegraph` and you're running in seconds. This matters more than people admit.

---

### The Rough Edges

#### 1. The Relation API Has Confusing Field Names

This one will bite you. The relation object has three fields — `source`, `target`, and `type` — but their semantics are not what you expect:

```python
# What you'd expect:
# r.source → the source object
# r.target → the target object
# r.type   → the relation type

# What ActiveGraph actually gives you:
# r.source → the relation TYPE (string like "authored_by")
# r.target → the SOURCE object ID
# r.type   → the TARGET object ID
```

This is exactly backwards from every graph database, RDF triple store, and property graph API in existence. Subject → Predicate → Object is the universal convention. ActiveGraph stores Predicate → Subject → Object. This caused real confusion while building the Inspector's graph endpoint and the demo server's seeding logic. I had to document it in persistent memory just to stop re-discovering it.

#### 2. `graph.objects()` Is Unsafe Inside Behaviors

Calling `graph.objects()` (the full collection scan) inside a behavior causes re-entrant graph access that can produce silent bugs or duplicates. The safe pattern is to pass object IDs through the behavior's context and call `graph.get_object(id)` for point lookups.

This is a real footgun for developers coming from normal Python — you naturally reach for the collection when you want to check for existing objects of a given type (e.g., "does a principal already exist for this sender?"). The workaround requires maintaining your own module-level dedup registry:

```python
# Pattern forced by the re-entrancy constraint
_principal_registry: dict[str, str] = {}  # sender_ref → object_id

@behavior(object_type="core/source")
def on_source(self, graph, obj):
    sender = normalize(obj.data["sender_ref"])
    if sender in _principal_registry:
        return  # dedup: don't re-create
    principal_id = graph.add_object("identity_auth/principal", {...})
    _principal_registry[sender] = principal_id
```

This works, but it leaks state between test runs unless you explicitly call a `clear_*_registry()` function in test fixtures. A built-in `graph.query(type=..., where=...)` method that's safe to call in behaviors would eliminate this pattern entirely.

#### 3. `@tool` Produces Non-Callable Objects

Decorating a method with `@tool` wraps it in a descriptor. The resulting attribute is NOT directly callable:

```python
@tool
def my_tool(self, graph, arg1):
    ...

# This crashes:
result = my_pack.my_tool(graph, "value")

# This works:
result = my_pack.my_tool._fn(graph, "value")
# or however the underlying callable is accessed
```

The workaround is to define a `_my_tool` method that does the actual work and call that from tests, while `@tool` is purely a declaration for the runtime's tool registry. This is non-obvious and the error message doesn't guide you there.

#### 4. `@behavior` Has No `description` Parameter

Every AI framework in 2025 asks "what does this do?" when registering capabilities. `@behavior` in ActiveGraph accepts `object_type` but not a description string. This makes it impossible to introspect what behaviors are registered and why at the pack API level. Not a blocker, but noticeably absent when building a runtime inspector.

#### 5. `Pack()` Requires Keyword Argument

```python
# Crashes:
pack = MyPack("my_pack")

# Works:
pack = MyPack(name="my_pack")
```

Minor, but bites you on first use and the error message doesn't tell you what's missing.

---

## Building the Pack Library: What Went Smoothly, What Didn't

### Went Smoothly
- Schema definition: clean, readable, easy to evolve
- Behavior chaining: `core/source` → `identity_auth/principal` → `identity_auth/auth_context` → `core/evaluation` wired up in ~30 minutes once the mental model clicked
- Namespace isolation: added `email` and `calendar` packs to the `identity`/`memory`/`comm` packs without any coupling issues
- Testing individual packs: instantiate the pack, add objects, call `run_until_idle()`, assert on graph state — clean and fast

### Didn't Go Smoothly

- The `packs/email/__init__.py` file shadows Python's stdlib `email` module (the package is literally named `email`). Anything downstream that does `import email` for MIME handling breaks with an unhelpful AttributeError. Had to `sys.path.remove()` the `packs/` directory before stdlib imports in the demo server. This is an unavoidable naming collision if you want your pack named "email" — not ActiveGraph's fault, but worth knowing.

### Correction: Persistence Is Built In

**An earlier draft of this report claimed ActiveGraph had "no persistence layer" and was "purely in-memory." That was wrong.** ActiveGraph ships an event-sourced persistence layer out of the box (`activegraph/store/`) with pluggable backends — `SQLiteEventStore` and `PostgresEventStore`. You opt in with `Runtime(graph, persist_to="state.sqlite")` (or a `sqlite:///` / `postgres://` URL) and every event is appended to the store as behaviors cascade. `Runtime.load(path)` resumes the most-recent run by **replaying the event log** to rebuild the graph projection (replay rebuilds objects/relations *without* re-firing behaviors, so resume is fast and side-effect-free). `rt.save_state()` flushes on demand. The one real caveat: any in-process registries your own packs maintain (dedup caches, etc.) are *not* part of the graph, so you must repopulate them from the replayed objects on resume — the demo server does this for its principal registry.

---

## Comparison to Other Agent Architectures

### vs. LangChain / LlamaIndex
These are LLM-centric frameworks. They start with "call an LLM" and add memory/tools/routing around it. ActiveGraph starts with "model your domain as a reactive graph" and LLM calls are optional. If your problem is "orchestrate prompts with some memory," use LangChain. If your problem is "build a coherent world model for a multi-domain agent," ActiveGraph gives you a much better primitive.

LangChain's memory is essentially a list of message strings. ActiveGraph's "memory" is a typed graph of objects with causal relations and a live behavior engine. The expressiveness difference is enormous.

### vs. AutoGen / CrewAI
These are agent-role frameworks: define agents, define workflows, watch agents hand off tasks. ActiveGraph doesn't have roles or workflows — it has behaviors that fire reactively. This is fundamentally different:
- AutoGen/CrewAI: explicit orchestration ("Agent A does X, then Agent B does Y")
- ActiveGraph: implicit emergence ("when object type X is added, behavior Y fires")

The reactive model scales better as complexity grows — you don't maintain a central orchestration script that breaks when you add a new capability. But it's harder to reason about for simple, linear tasks.

### vs. Semantic Kernel (Microsoft)
Most similar in philosophy. Semantic Kernel also has a plugin/skill model, typed memory, and a graph-like concept of state. ActiveGraph is lighter and more Pythonic. Both ship persistence — ActiveGraph via its event-sourced SQLite/Postgres store, SK via its memory/vector connectors; SK still leads on vector search and streaming. ActiveGraph's behavior cascade is more powerful than SK's function chaining.

### vs. Traditional Knowledge Graphs (Neo4j, RDFLib)
Knowledge graphs store facts; they don't react to them. ActiveGraph is a knowledge graph with triggers. This is the key innovation: the graph is both a data store and a rule engine. You don't poll the graph for new facts and run policies manually — the policies fire automatically when the facts arrive. This is a substantially better model for event-driven agent systems.

### vs. ECS Frameworks (esper, pygame-ecs)
ActiveGraph is conceptually the closest to an ECS: packs = systems, objects = entities. The difference is that ECS systems run on a tick (every frame), while ActiveGraph behaviors fire on mutation. Mutation-driven > tick-driven for agent systems because you're not wasting CPU polling for changes that haven't happened.

---

## Building the Inspector UI

The Inspector is a React + Vite app that visualizes live graph state from a running ActiveGraph runtime. Six pages: Dashboard, Graph, Trace, Packs, Frames, Chat.

**What helped:** The ActiveGraph demo server exposes clean JSON endpoints (`/graph`, `/trace`, `/packs`, `/summary`, `/frames`). The data shapes are predictable. React Query polls at 3-second intervals, which is fast enough to feel live without hammering the server.

**What was awkward:** The `/graph` endpoint returns objects and relations, but the relation field naming issue (see above) means the frontend has to map `r.source` → `relation_type` and `r.target` → `source_object_id`. That's counterintuitive in display code too — you end up writing `relation.source` when you mean "what type of relation is this?" rather than "what is this relation's source node?"

**The Frames page is always empty** in the demo — `activegraph` v1.0.5.post2 doesn't appear to populate frames via the API surface exposed by the demo server. Either the concept isn't implemented yet or it requires a different invocation pattern not covered in documentation.

---

## What the Behavior Cascade Feels Like in Practice

This is the thing that's hard to explain until you've built with it.

You're writing a comm-processor pack that handles incoming messages. A message arrives as `comm/message`. You don't write a function that says "check if the sender exists, if not create a principal, then check their auth context, then evaluate permissions." You write:

```
@behavior(object_type="comm/message")
def on_message(self, graph, obj):
    sender = obj.data["from"]
    graph.add_object("core/source", {"sender_ref": sender, ...})
    # that's it

@behavior(object_type="core/source")   # in identity pack
def on_source(self, graph, obj):
    # resolve principal, maybe add to graph
    ...

@behavior(object_type="identity_auth/principal")  # still in identity pack
def on_principal(self, graph, obj):
    # build auth context
    ...
```

The cascade is implicit. Each behavior does one thing. The composition is automatic.

This feels genuinely good to write. It's like database triggers but without the operational horror — they're in-process, synchronous, testable, and composable across packs without shared mutable state.

The flip side: **debugging unexpected cascades** is hard. If adding object A triggers behavior B which triggers behavior C which triggers behavior D which you didn't expect, finding that chain requires either trace instrumentation or carefully reading behavior registrations across all loaded packs. There's no built-in cascade visualizer (though that's exactly what the Trace page in the Inspector attempts to be).

---

## Production Readiness Assessment

**Suitable for:** research prototypes, internal demos, agent system PoCs, offline event processing, multi-domain reasoning kernels.

**Not yet suitable for (in its current state):** production multi-tenant services (no built-in transaction semantics across concurrent writers), high-throughput event ingestion (single-threaded behavior dispatch). Note that graph replay and audit trails *are* covered — the event-sourced store gives you both for free.

The runtime is conceptually solid, and persistence is already covered by the built-in event-sourced store. The API surface needs polish. The remaining gaps for production are concurrent access (multi-writer transaction semantics), observability hooks, and schema migration support.

---

## Notes for the ActiveGraph Developer

These are observations, not demands — offered in the spirit of someone who just spent serious time inside the thing.

**On the relation field naming:** Strongly consider `relation.relation_type`, `relation.from_id`, `relation.to_id` (or `r.predicate`, `r.subject_id`, `r.object_id` for the RDF crowd). The current `source`/`target`/`type` mapping is semantically inverted from every other graph API and will reliably confuse developers on first contact.

**On `graph.objects()` in behaviors:** Either make it safe (via snapshot semantics — behaviors operate on a snapshot of the graph at the time they were triggered), or raise a clear `BehaviorReentrancyError` with an actionable message. Silent dedup bugs are the worst kind.

**On the `@tool` DX:** The tool decorator should either make the method directly callable (calling via `_fn` is too internal-feeling) or document prominently that `@tool` is purely declarative and you call the underlying method directly in non-runtime contexts.

**On persistence:** This is already well-handled by the event-sourced store (`Runtime(graph, persist_to=...)` + `Runtime.load(path)`) — credit where due. The remaining ask is documentation discoverability: it took digging through `activegraph/store/` to realize this existed. A prominent "Persistence" section in the README, plus guidance on the resume-time gotcha (in-process registries maintained by your own packs aren't part of the replayed graph and must be rebuilt), would save builders real time.

**On observability:** A `graph.subscribe(callback)` or `graph.on_mutation(callback)` hook would make the Inspector trivially accurate in real-time rather than polling. It would also make it possible to build reactive UIs, pub/sub bridges, and audit logs without patching the internals.

**On the Frames concept:** The API exposes a `/frames` endpoint and the object model references frames, but it's unclear from the package what creates frames, when, and how to inspect them. A short example in the README showing frame creation and retrieval would resolve this.

**On documentation:** The biggest gap is worked examples of multi-pack composition — what does a 3-pack system look like, how do packs share type references safely, how do you handle pack load order? The single-pack examples in the README are clear; the multi-pack story is underspecified.

---

## Summary

ActiveGraph is a genuinely interesting primitive. The reactive object graph model is better suited to multi-domain agent systems than any LLM-centric framework I've worked with. The pack composition model is clean. The behavior cascade is powerful and — once the mental model clicks — a joy to write.

The rough edges are real but fixable: the relation API naming, the re-entrancy footgun, the `@tool` callability, and the under-documented (but present and capable) persistence layer. None of them are architectural — they're polish issues on top of a sound core.

If you're building an agent system that needs to reason about structured world state across multiple domains (identity, memory, communication, permissions) and you want your logic to be composable, testable, and reactive rather than monolithic and procedural — ActiveGraph is worth taking seriously. Just budget time to learn the quirks documented above before diving into domain logic.

---

*Report generated after building ~2500 lines of pack library code, a Python HTTP demo server, an Express TypeScript API proxy, and a full React inspector UI against activegraph v1.0.5.post2.*
