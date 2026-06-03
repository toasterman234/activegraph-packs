"""ActiveGraph Bundles.

Pre-assembled pack collections for common assistant configurations.
A bundle is a preset list of packs + default settings, not a new pack.

Available bundles (as packs become available):
  ASSISTANT_BUNDLE      — core infrastructure (core, tool_gateway, secrets, memory_gateway, agent_profile, identity_auth, communication, chat)
  EMAIL_ASSISTANT_BUNDLE — assistant + email + entity
  VC_BUNDLE             — email assistant + diligence bridge + vc + meeting
  RESEARCH_BUNDLE       — core + tool_gateway + memory_gateway + communication + chat + research

Usage:
    from bundles.assistant import ASSISTANT_BUNDLE, build_assistant
    rt = build_assistant()
    rt.run_goal("...")
"""
