---
trigger: model_decision
description: form-validation
---

Name: form-validation

Content:

1. Always use React Hook Form + Zod
2. Schema pattern:

```typescript
const schema = z.object({
  field: z.string().min(1, "Field required"),
});
```

3. Form pattern:

```typescript
const {
  register,
  handleSubmit,
  formState: { errors },
} = useForm({
  resolver: zodResolver(schema),
});
```

4. Show field-level errors immediately
5. Show form-level errors in toast
6. Disable submit button while submitting
7. Show loading indicator on submit button
