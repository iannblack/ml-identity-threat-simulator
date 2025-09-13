SELECT role, member, COUNT(*) AS occurrences FROM `security.iam_bindings_audit` GROUP BY role, member ORDER BY occurrences DESC;
