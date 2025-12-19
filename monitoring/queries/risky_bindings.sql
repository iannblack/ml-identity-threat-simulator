-- Example query for SOC table `security.iam_bindings_audit`
SELECT role, member, COUNT(*) AS occurrences
FROM `security.iam_bindings_audit`
WHERE member IN ('allUsers','allAuthenticatedUsers')
   OR role IN ('roles/owner','roles/editor')
GROUP BY role, member
ORDER BY occurrences DESC;
