# Contracts

This directory contains machine-readable schemas for interfaces exchanged across components. Schemas define expected structure; they do not by themselves enforce authorization or prove runtime compatibility.

## Change guidance

When changing a contract, identify every producer and consumer, update their tests, and validate the schema with the repository's documented command. Preserve backward compatibility or document the migration explicitly.
