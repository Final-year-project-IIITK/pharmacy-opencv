import { describe, expect, it } from 'vitest';
import { filterMedicinesByQuery, getExpirySnapshot, splitProcurementRequests, splitSaleInvoicesByDay, upsertMedicineInList } from './App';

describe('splitProcurementRequests', () => {
    it('separates requests awaiting approval from sent requests', () => {
        const requests = [
            { id: 1, status: 'pending_review' },
            { id: 2, status: 'sent' },
        ];

        const result = splitProcurementRequests(requests);

        expect(result.awaitingApproval.map((request) => request.id)).toEqual([1]);
        expect(result.sent.map((request) => request.id)).toEqual([2]);
    });
});

describe('getExpirySnapshot', () => {
    it('marks expired stock as black', () => {
        const result = getExpirySnapshot('2020-01-01');

        expect(result.expiryBand).toBe('black');
        expect(result.expiryLabel).toBe('Expired');
    });

    describe('upsertMedicineInList', () => {
        const medicine = (id: number, name: string) => ({
            id,
            name,
            sku: `MED-${id}`,
            category: 'Test',
            unit: 'tablet',
            reorder_level: 5,
            ideal_stock: 20,
            active: true,
            created_at: '2026-01-01T00:00:00',
        });

        it('adds new medicines and replaces edits without duplicating entries', () => {
            const existing = medicine(1, 'Beta');
            const created = upsertMedicineInList([existing], medicine(2, 'Alpha'));

            expect(created.created).toBe(true);
            expect(created.medicines.map((entry) => entry.name)).toEqual(['Alpha', 'Beta']);

            const edited = upsertMedicineInList(created.medicines, medicine(1, 'Aardvark'));
            expect(edited.created).toBe(false);
            expect(edited.medicines.map((entry) => entry.name)).toEqual(['Aardvark', 'Alpha']);
            expect(edited.medicines).toHaveLength(2);
        });
    });

    describe('splitSaleInvoicesByDay', () => {
        it('separates local-day invoices from earlier bills, including UTC timestamps', () => {
            const now = new Date(2025, 3, 10, 12);
            const startOfToday = new Date(2025, 3, 10).toISOString();
            const previousDay = new Date(2025, 3, 9, 23, 59).toISOString();
            const invoice = (invoice_number: string, sold_at: string) => ({
                invoice_number,
                buyer_name: 'Test buyer',
                medicine_name: 'Medicine',
                sku: 'MED-001',
                batch_number: 'BATCH-001',
                quantity: 1,
                unit_price: 10,
                total_amount: 10,
                sold_by: 'pharmacist',
                sold_at,
                items: [],
            });

            const result = splitSaleInvoicesByDay([
                invoice('TODAY', startOfToday),
                invoice('PREVIOUS', previousDay),
            ], now);

            expect(result.today.map((entry) => entry.invoice_number)).toEqual(['TODAY']);
            expect(result.previous.map((entry) => entry.invoice_number)).toEqual(['PREVIOUS']);
        });
    });
    describe('filterMedicinesByQuery', () => {
        const medicines = [
            { name: 'Paracetamol', sku: 'MED-001', category: 'Analgesic', description: 'Pain and fever relief' },
            { name: 'Amoxicillin', sku: 'MED-002', category: 'Antibiotic', description: null },
        ];

        it('matches medicine names, SKUs, categories, and descriptions without case sensitivity', () => {
            expect(filterMedicinesByQuery(medicines, 'med-002')).toEqual([medicines[1]]);
            expect(filterMedicinesByQuery(medicines, 'FEVER')).toEqual([medicines[0]]);
            expect(filterMedicinesByQuery(medicines, ' antibiotic ')).toEqual([medicines[1]]);
        });

        it('returns all medicines for an empty query and none for an unmatched query', () => {
            expect(filterMedicinesByQuery(medicines, '  ')).toEqual(medicines);
            expect(filterMedicinesByQuery(medicines, 'unknown')).toEqual([]);
        });
    });

    it('marks disposed stock as black even when the date is in the future', () => {
        const result = getExpirySnapshot('2099-01-01', 'disposed');

        expect(result.expiryBand).toBe('black');
        expect(result.expiryLabel).toBe('Disposed');
    });

    it('marks stock expiring within ninety days as red', () => {
        const expiry = new Date();
        expiry.setDate(expiry.getDate() + 30);

        expect(getExpirySnapshot(expiry.toISOString().slice(0, 10)).expiryBand).toBe('red');
    });
});
