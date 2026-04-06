from django.db import migrations, models
import django.db.models.deletion


def backfill_allocations(apps, schema_editor):
    """Create one BudgetAllocation per existing Transaction with budget_account set."""
    Transaction = apps.get_model("accounts", "Transaction")
    BudgetAllocation = apps.get_model("accounts", "BudgetAllocation")

    allocations = []
    for txn in Transaction.objects.filter(budget_account__isnull=False).iterator():
        allocations.append(
            BudgetAllocation(
                transaction=txn,
                budget_account=txn.budget_account,
                amount=txn.amount_spent,
                description="",
            )
        )
    BudgetAllocation.objects.bulk_create(allocations, batch_size=500)


def reverse_backfill(apps, schema_editor):
    """Copy allocations back to Transaction.budget_account for rollback."""
    BudgetAllocation = apps.get_model("accounts", "BudgetAllocation")
    Transaction = apps.get_model("accounts", "Transaction")

    for alloc in BudgetAllocation.objects.select_related("transaction").iterator():
        Transaction.objects.filter(pk=alloc.transaction_id).update(
            budget_account=alloc.budget_account_id
        )


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0013_add_transaction_date_index"),
    ]

    operations = [
        # Step 1: Create BudgetAllocation table
        migrations.CreateModel(
            name="BudgetAllocation",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "amount",
                    models.DecimalField(decimal_places=2, max_digits=10),
                ),
                (
                    "description",
                    models.CharField(blank=True, max_length=200),
                ),
                (
                    "transaction",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="allocations",
                        to="accounts.transaction",
                    ),
                ),
                (
                    "budget_account",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        related_name="allocations",
                        to="accounts.budgetaccount",
                    ),
                ),
            ],
        ),
        # Step 2: Backfill data
        migrations.RunPython(backfill_allocations, reverse_backfill),
        # Step 3: Remove budget_account FK from Transaction
        migrations.RemoveField(
            model_name="transaction",
            name="budget_account",
        ),
    ]
